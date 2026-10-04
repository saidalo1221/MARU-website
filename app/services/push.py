"""Web Push notifications (PRD ТЗ№1 §39: abandoned-cart "push", §38 status updates).

A signed-in customer opts in from their account page; the browser hands us a subscription (endpoint + keys).
We send an encrypted message to the browser's push service, signed with the VAPID key pair from .env
(VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY / VAPID_SUBJECT; create them with scripts/generate_vapid.py).
Sends are background jobs when JOBS_ASYNC is on. A subscription the push service reports as gone (404/410)
is deleted. iPhones only receive web push when the site has been added to the home screen (Apple's rule).
"""

import json
import logging
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.push_subscription import PushSubscription
from app.services.jobs import PermanentJobError, enqueue, job_handler

logger = logging.getLogger("maru.push")


def enabled() -> bool:
    return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY and settings.VAPID_SUBJECT)


def subscriptions_of(db: Session, user_id: int) -> list:
    return list(db.execute(select(PushSubscription).where(PushSubscription.user_id == user_id)).scalars())


def _send_one(subscription: dict, message: dict) -> None:
    from pywebpush import webpush

    webpush(
        subscription_info=subscription,
        data=json.dumps(message, ensure_ascii=False),
        vapid_private_key=settings.VAPID_PRIVATE_KEY,
        vapid_claims={"sub": settings.VAPID_SUBJECT},
        ttl=86400,
        timeout=10,
    )


def _as_info(sub: PushSubscription) -> dict:
    return {"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}}


def notify_user(db: Optional[Session], user_id: Optional[int], title: str, body: str, url: str = "/") -> int:
    """Pushes a message to every device of the user. Returns how many were sent or queued. Never raises."""
    if not enabled() or db is None or user_id is None:
        return 0
    try:
        subs = subscriptions_of(db, user_id)
        message = {"title": title[:100], "body": body[:200], "url": url}
        count = 0
        for sub in subs:
            if settings.JOBS_ASYNC:
                enqueue(db, "push.send", {"subscription_id": sub.id, "message": message})
                count += 1
            elif _deliver(db, sub.id, message):
                count += 1
        return count
    except Exception:  # noqa: BLE001 - a push problem must never break the order or the cart
        logger.exception("Could not push to user %s", user_id)
        return 0


def _deliver(db: Session, subscription_id: int, message: dict) -> bool:
    """One send. Returns True on success; removes dead subscriptions; raises for retryable failures."""
    from pywebpush import WebPushException

    sub = db.get(PushSubscription, subscription_id)
    if sub is None:
        return False
    try:
        _send_one(_as_info(sub), message)
        return True
    except WebPushException as exc:
        status = getattr(exc.response, "status_code", None)
        if status in (404, 410):  # the browser unsubscribed or the subscription expired
            db.execute(delete(PushSubscription).where(PushSubscription.id == subscription_id))
            db.commit()
            return False
        logger.warning("Push refused (HTTP %s)", status)
        return False


@job_handler("push.send")
def _send_job(db: Session, payload: dict) -> None:
    from pywebpush import WebPushException

    sub = db.get(PushSubscription, payload["subscription_id"])
    if sub is None:
        raise PermanentJobError("The subscription no longer exists")
    try:
        _send_one(_as_info(sub), payload["message"])
    except WebPushException as exc:
        status = getattr(exc.response, "status_code", None)
        if status in (404, 410):
            db.delete(sub)
            db.commit()
            raise PermanentJobError("The browser unsubscribed; subscription removed") from None
        if status is not None and 400 <= status < 500 and status != 429:
            raise PermanentJobError(f"The push service refused the message (HTTP {status})") from None
        raise RuntimeError(f"Push failed (HTTP {status or '-'})") from None
