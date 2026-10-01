"""Server-side forwarding of analytics events to Google Analytics 4 through the Measurement Protocol
(PRD ТЗ№4 §45-49). Configure GA4_MEASUREMENT_ID and GA4_API_SECRET in .env (the secret is created in
GA4 > Admin > Data streams > Measurement Protocol API secrets). Without them nothing is sent.

What is sent: the event name, scalar parameters, and an anonymous `client_id` (a hash of the visitor
session or user id - never an email, phone or name). Staff events (admin_login) are never forwarded.
With GA4_DEBUG=true events go to Google's validation endpoint, which checks them but records nothing."""

import hashlib
import logging
import re
from typing import Optional

import requests

from app.config import settings
from app.services.jobs import enqueue, job_handler

logger = logging.getLogger("maru.ga4")

COLLECT_URL = "https://www.google-analytics.com/mp/collect"
DEBUG_URL = "https://www.google-analytics.com/debug/mp/collect"

_NEVER_FORWARD = {"admin_login"}
_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,39}$")
# Our property names -> the names GA4's recommended events expect.
_RENAME = {"order_id": "transaction_id"}
_MAX_PARAMS = 25
_ITEM_KEYS = ("item_id", "item_name", "price", "quantity")


def enabled() -> bool:
    return bool(settings.GA4_MEASUREMENT_ID and settings.GA4_API_SECRET)


def client_id(user_id: Optional[int], session_id: Optional[str]) -> str:
    """Stable anonymous id: the same visitor/user always maps to the same value, but it cannot be
    turned back into the session token or user id."""
    raw = f"user:{user_id}" if user_id is not None else f"session:{session_id or 'anonymous'}"
    return hashlib.sha256(f"{settings.SECRET_KEY}|{raw}".encode()).hexdigest()[:32]


def build_payload(event_name: str, user_id: Optional[int], session_id: Optional[str], properties: dict) -> Optional[dict]:
    if event_name in _NEVER_FORWARD or not _NAME.match(event_name):
        return None
    params: dict = {}
    for key, value in (properties or {}).items():
        if key == "items" and isinstance(value, list):  # ecommerce items (also what remarketing audiences are built from)
            params["items"] = [
                {k: (float(v) if k == "price" else v) for k, v in item.items() if k in _ITEM_KEYS and v is not None}
                for item in value[:20] if isinstance(item, dict)
            ]
            continue
        key = _RENAME.get(key, key)
        if not _NAME.match(key) or isinstance(value, (dict, list, bool)) or value is None:
            continue
        if key == "value":
            try:
                value = float(value)
            except (TypeError, ValueError):
                continue
        elif isinstance(value, str):
            value = value[:100]
        params[key] = value
        if len(params) >= _MAX_PARAMS:
            break
    return {"client_id": client_id(user_id, session_id), "events": [{"name": event_name, "params": params}]}


def send(payload: dict) -> bool:
    """One Measurement Protocol call. Returns True when Google accepted it (or, in debug mode, when
    it validated with no messages). Raises requests.RequestException on a network/HTTP failure so a
    queued job can retry; callers that must not fail catch it."""
    url = DEBUG_URL if settings.GA4_DEBUG else COLLECT_URL
    response = requests.post(
        url,
        params={"measurement_id": settings.GA4_MEASUREMENT_ID, "api_secret": settings.GA4_API_SECRET},
        json=payload,
        timeout=5,
    )
    response.raise_for_status()
    if settings.GA4_DEBUG:
        messages = response.json().get("validationMessages", [])
        if messages:
            logger.warning("GA4 rejected the event: %s", messages)
        return not messages
    return True


def forward(event_name: str, user_id: Optional[int], session_id: Optional[str], properties: dict, db=None) -> None:
    """Fire-and-forget from the request path: queued when JOBS_ASYNC is on (retried by the worker),
    otherwise sent inline with a short timeout. Never raises."""
    if not enabled():
        return
    payload = build_payload(event_name, user_id, session_id, properties)
    if payload is None:
        return
    if settings.JOBS_ASYNC and db is not None:
        enqueue(db, "ga4.send", payload)
        return
    try:
        send(payload)
    except requests.RequestException:
        # Do not log the exception text: it contains the request URL, which carries the API secret.
        logger.warning("GA4 forward failed for %s (network or HTTP error)", event_name)
    except Exception:  # noqa: BLE001
        logger.exception("GA4 forward failed for %s", event_name)


@job_handler("ga4.send")
def _send_job(db, payload: dict) -> None:
    try:
        send(payload)
    except requests.RequestException as exc:
        # str(exc) would carry the request URL and with it the API secret into jobs.last_error.
        raise RuntimeError(f"GA4 request failed ({type(exc).__name__})") from None
