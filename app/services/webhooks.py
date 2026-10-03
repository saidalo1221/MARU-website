"""Signed inbound webhooks (PRD ТЗ№4 §50-51). The sender signs `"<timestamp>.<raw body>"` with the
shared secret of its provider (WEBHOOK_SECRETS) using HMAC-SHA256 and sends the hex digest in
X-Maru-Signature, the unix time in X-Maru-Timestamp and a unique id in X-Maru-Event-Id. We verify
the signature and freshness, remember the event id (so redelivery is ignored), and queue the
payload for the worker - the sender gets its 202 immediately."""

import hashlib
import hmac
import json
import logging
import time
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.webhook_event import WebhookEvent
from app.services.jobs import enqueue, job_handler

logger = logging.getLogger("maru.webhooks")

TOLERANCE_SECONDS = 300


def provider_secret(provider: str) -> Optional[str]:
    try:
        secrets = json.loads(settings.WEBHOOK_SECRETS or "{}")
    except ValueError:
        logger.error("WEBHOOK_SECRETS is not valid JSON")
        return None
    secret = secrets.get(provider) if isinstance(secrets, dict) else None
    return secret or None


def sign(secret: str, timestamp: str, body: bytes) -> str:
    return hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()


def verify(secret: str, timestamp: str, signature: str, body: bytes, now: Optional[float] = None) -> bool:
    try:
        age = abs((now if now is not None else time.time()) - float(timestamp))
    except (TypeError, ValueError):
        return False
    return age <= TOLERANCE_SECONDS and hmac.compare_digest(sign(secret, timestamp, body), signature or "")


def accept(db: Session, provider: str, event_id: str, body: bytes) -> bool:
    """Stores the event and queues it. Returns False when this event id was already accepted."""
    event = WebhookEvent(provider=provider, event_id=event_id)
    db.add(event)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return False
    job = enqueue(
        db, "webhook.received",
        {"provider": provider, "event_id": event_id, "body": body.decode("utf-8", "replace")},
        commit=False,
    )
    event.job_id = job.id
    db.commit()
    return True


@job_handler("webhook.received")
def _handle_received(db: Session, payload: dict) -> None:
    # No provider has a connector yet (they need vendor docs/credentials); the event is
    # kept in the queue history so a connector can be added without losing deliveries.
    logger.info("Webhook %s/%s processed (no connector registered)", payload["provider"], payload["event_id"])
