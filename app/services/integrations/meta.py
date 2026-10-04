"""Server-side forwarding of analytics events to the Meta Conversions API (PRD ТЗ№4 §45-49).
Configure META_PIXEL_ID and META_CAPI_TOKEN in .env (token: Events Manager > the pixel > Settings >
Conversions API > Generate access token). Without them nothing is sent. Put a code from Events
Manager > Test events in META_TEST_EVENT_CODE to see events there without counting them.

What is sent: the Meta event name, a timestamp, a dedupe id, scalar custom data (value/currency...)
and one hashed `external_id` (visitor session or user id). No email, phone, name or address, so
Meta's matching is weak; add those (SHA-256 hashed, consent permitting) to improve it."""

import hashlib
import logging
import time
from typing import Optional

import requests

from app.config import settings
from app.services.jobs import enqueue, job_handler

logger = logging.getLogger("maru.meta")

API_VERSION = "v21.0"
# Our (GA4-shaped) event names -> Meta standard events. Anything not listed is not forwarded.
EVENT_MAP = {
    "purchase": "Purchase",
    "add_to_cart": "AddToCart",
    "begin_checkout": "InitiateCheckout",
    "sign_up": "CompleteRegistration",
    "generate_lead": "Lead",
    "add_to_wishlist": "AddToWishlist",
    "view_item": "ViewContent",
    "search": "Search",
}
_CUSTOM_KEYS = {"value", "currency", "order_id", "content_name", "search_string", "num_items"}


def enabled() -> bool:
    return bool(settings.META_PIXEL_ID and settings.META_CAPI_TOKEN)


def _hash(value: str) -> str:
    return hashlib.sha256(f"{settings.SECRET_KEY}|{value}".encode()).hexdigest()


def build_payload(event_name: str, user_id: Optional[int], session_id: Optional[str], properties: dict, event_time: Optional[int] = None) -> Optional[dict]:
    meta_name = EVENT_MAP.get(event_name)
    if meta_name is None:
        return None
    props = properties or {}
    custom: dict = {}
    for key in _CUSTOM_KEYS:
        value = props.get(key)
        if value is None or isinstance(value, (dict, list, bool)):
            continue
        if key == "value":
            try:
                value = float(value)
            except (TypeError, ValueError):
                continue
        elif isinstance(value, str):
            value = value[:100]
        custom[key] = value
    items = [i for i in (props.get("items") or []) if isinstance(i, dict) and i.get("item_id")][:20]
    if items:  # what dynamic product ads / remarketing audiences use
        custom["content_type"] = "product"
        custom["content_ids"] = [str(i["item_id"]) for i in items]
        custom["contents"] = [{"id": str(i["item_id"]), "quantity": int(i.get("quantity") or 1), "item_price": float(i.get("price") or 0)} for i in items]
        custom["num_items"] = sum(int(i.get("quantity") or 1) for i in items)
    if meta_name == "Purchase" and ("value" not in custom or "currency" not in custom):
        return None  # Meta rejects a Purchase without both
    who = f"user:{user_id}" if user_id is not None else f"session:{session_id or 'anonymous'}"
    when = event_time or int(time.time())
    event_id = f"{event_name}-{props.get('order_id') or _hash(f'{who}|{when}')[:16]}"
    body: dict = {
        "data": [{
            "event_name": meta_name,
            "event_time": when,
            "event_id": event_id,  # lets Meta drop a duplicate if the browser pixel reports the same event
            "action_source": "website",
            "user_data": {"external_id": [_hash(who)]},
            "custom_data": custom,
        }]
    }
    if settings.META_TEST_EVENT_CODE:
        body["test_event_code"] = settings.META_TEST_EVENT_CODE
    return body


def send(payload: dict) -> bool:
    """One Conversions API call; raises requests.RequestException on a network/HTTP error."""
    response = requests.post(
        f"https://graph.facebook.com/{API_VERSION}/{settings.META_PIXEL_ID}/events",
        headers={"Authorization": f"Bearer {settings.META_CAPI_TOKEN}"},
        json=payload,
        timeout=5,
    )
    if response.status_code >= 400:
        # Meta explains the problem in the body (it never echoes the token); keep that for diagnosis.
        logger.warning("Meta rejected the event (HTTP %s): %s", response.status_code, response.text[:300])
    response.raise_for_status()
    return True


def forward(event_name: str, user_id: Optional[int], session_id: Optional[str], properties: dict, db=None) -> None:
    """Called after an analytics event is stored. Queued when JOBS_ASYNC is on, otherwise sent inline.
    Never raises."""
    if not enabled():
        return
    payload = build_payload(event_name, user_id, session_id, properties)
    if payload is None:
        return
    if settings.JOBS_ASYNC and db is not None:
        enqueue(db, "meta.send", payload)
        return
    try:
        send(payload)
    except requests.RequestException as exc:
        logger.warning("Meta forward failed for %s (%s)", event_name, type(exc).__name__)
    except Exception:  # noqa: BLE001
        logger.exception("Meta forward failed for %s", event_name)


@job_handler("meta.send")
def _send_job(db, payload: dict) -> None:
    try:
        send(payload)
    except requests.RequestException as exc:
        raise RuntimeError(f"Meta request failed ({type(exc).__name__}: HTTP {getattr(exc.response, 'status_code', '-')})") from None
