"""Outbound webhooks (PRD ТЗ№1 §37): tell other systems (ERP, CRM, a warehouse tool) when something happens.

Each delivery is a job (`webhook.deliver`), so it is retried with backoff and ends in the dead-letter list if
the receiver keeps failing. The request carries the same signature scheme the platform expects on inbound
webhooks, so one verification routine serves both directions:

    X-Maru-Event       order.paid
    X-Maru-Event-Id    unique id of this event (receivers can drop repeats)
    X-Maru-Timestamp   unix seconds
    X-Maru-Signature   hex HMAC-SHA256(secret, "<timestamp>.<raw body>")

Body: {"id", "event", "created_at", "data": {...}}. Order data includes the customer's name, e-mail and
phone because the usual receivers (ERP/CRM) need them; point endpoints only at systems you own.
"""

import ipaddress
import json
import logging
import socket
import time
import uuid
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.webhook_endpoint import EVENTS, WebhookEndpoint
from app.services.jobs import PermanentJobError, enqueue, job_handler, run_pending
from app.services.webhooks import sign

logger = logging.getLogger("maru.webhooks.out")


class UnsafeURLError(ValueError):
    pass


def check_url(url: str) -> None:
    """https only, and not an internal address (so a mistyped or malicious URL cannot be used to probe the
    private network or the cloud metadata service). WEBHOOK_ALLOW_PRIVATE_URLS=true relaxes both for dev."""
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http") or not parsed.hostname:
        raise UnsafeURLError("The URL must start with https://")
    if settings.WEBHOOK_ALLOW_PRIVATE_URLS:
        return
    if parsed.scheme != "https":
        raise UnsafeURLError("The URL must use https")
    try:
        addresses = {ai[4][0] for ai in socket.getaddrinfo(parsed.hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)}
    except socket.gaierror as exc:
        raise UnsafeURLError("The host name cannot be resolved") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise UnsafeURLError("The URL points to an internal network address")


def _subscribes(endpoint: WebhookEndpoint, event: str) -> bool:
    wanted = {e.strip() for e in (endpoint.events or "*").split(",") if e.strip()}
    return "*" in wanted or event in wanted


def order_data(order) -> dict:
    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status.value,
        "payment_status": order.payment_status.value if order.payment_status else None,
        "currency": order.currency,
        "subtotal": str(order.subtotal_amount),
        "discount": str(order.discount_amount),
        "tax": str(order.tax_amount),
        "delivery": str(order.delivery_amount),
        "total": str(order.total_amount),
        "payment_method": order.payment_method,
        "delivery_method": order.delivery_method,
        "source": order.source,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "customer": {
            "first_name": order.first_name, "last_name": order.last_name, "email": order.email, "phone": order.phone,
            "country": order.country, "city": order.city, "address": order.address_line,
        },
        "items": [
            {"sku": i.sku_code_snapshot, "name": i.product_name_snapshot, "quantity": i.quantity,
             "unit_price": str(i.unit_price), "line_total": str(i.line_total)}
            for i in order.items
        ],
    }


def emit(db: Session, event: str, data: dict, commit: bool = True) -> int:
    """Queues one delivery per subscribed endpoint; returns how many. Never raises: webhooks must not break
    the action that triggered them. With JOBS_ASYNC off (no worker) the queued deliveries run right away."""
    try:
        endpoints = db.execute(select(WebhookEndpoint).where(WebhookEndpoint.is_active.is_(True))).scalars().all()
        targets = [e for e in endpoints if _subscribes(e, event)]
        if not targets:
            return 0
        event_id = uuid.uuid4().hex
        body = json.dumps(
            {"id": event_id, "event": event, "created_at": datetime.now(timezone.utc).isoformat(), "data": data},
            default=str,
        )
        for endpoint in targets:
            enqueue(db, "webhook.deliver", {"endpoint_id": endpoint.id, "event": event, "event_id": event_id, "body": body},
                    dedupe_key=f"wh:{endpoint.id}:{event_id}", commit=commit)
        if commit and not settings.JOBS_ASYNC:
            run_pending(db, "inline", limit=len(targets))
        return len(targets)
    except Exception:  # noqa: BLE001
        logger.exception("Could not queue webhook %s", event)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return 0


def deliver(endpoint: WebhookEndpoint, event: str, event_id: str, body: str) -> int:
    """One signed POST. Returns the HTTP status; raises requests.RequestException on a network failure."""
    check_url(endpoint.url)
    timestamp = str(int(time.time()))
    response = requests.post(
        endpoint.url,
        data=body.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "MARU-Webhooks/1",
            "X-Maru-Event": event,
            "X-Maru-Event-Id": event_id,
            "X-Maru-Timestamp": timestamp,
            "X-Maru-Signature": sign(endpoint.secret, timestamp, body.encode("utf-8")),
        },
        timeout=10,
        allow_redirects=False,  # a redirect could lead to an internal address that check_url never saw
    )
    return response.status_code


@job_handler("webhook.deliver")
def _deliver_job(db: Session, payload: dict) -> None:
    endpoint: Optional[WebhookEndpoint] = db.get(WebhookEndpoint, payload["endpoint_id"])
    if endpoint is None or not endpoint.is_active:
        raise PermanentJobError("The webhook endpoint was removed or switched off")
    try:
        status = deliver(endpoint, payload["event"], payload["event_id"], payload["body"])
        error = None if 200 <= status < 300 else f"HTTP {status}"
    except UnsafeURLError as exc:
        endpoint.last_error = str(exc)[:300]
        db.commit()
        raise PermanentJobError(str(exc)) from None
    except requests.RequestException as exc:
        status, error = None, f"Network error ({type(exc).__name__})"
    endpoint.last_delivery_at = datetime.now(timezone.utc).replace(tzinfo=None)
    endpoint.last_status_code = status
    endpoint.last_error = error
    db.commit()
    if error is None:
        return
    if status is not None and 400 <= status < 500 and status not in (408, 429):
        raise PermanentJobError(f"The receiver refused the event ({error})")
    raise RuntimeError(error)


def emit_for_order(db: Session, event: str, order) -> int:
    """Convenience: order.* / payment.* events carry the order snapshot."""
    try:
        return emit(db, event, order_data(order))
    except Exception:  # noqa: BLE001
        logger.exception("Could not build webhook data for order %s", getattr(order, "id", "?"))
        return 0


STATUS_EVENTS = {
    "PAID": ("order.paid", "payment.success"),
    "CANCELLED": ("order.cancelled",),
    "SHIPPED": ("order.shipped",),
    "DELIVERED": ("order.delivered",),
    "PAYMENT_FAILED": ("payment.failed",),
}

__all__ = ["EVENTS", "emit", "emit_for_order", "check_url", "UnsafeURLError", "STATUS_EVENTS"]
