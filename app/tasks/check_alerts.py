"""Operational alerts by email (PRD ТЗ№4 §67). Schedule every 10-15 minutes:

    python -m app.tasks.check_alerts

Needs ALERT_EMAIL (and working SMTP). Checks, with thresholds from settings:
  - dead_letter:<integration>  an integration call exhausted its retries
  - retry_backlog              too many integration calls waiting for a retry
  - sync_lag:<integration>     the oldest unresolved integration failure is too old
  - payment_failures           too many PAYMENT_FAILED orders in the last hour

The same alert is not repeated within ALERT_COOLDOWN_MINUTES; the last send is
remembered as an audit-log row (action "alert_sent"). Assumes the database
clock is UTC, like the other time-window queries in the app.

Not covered: rejected webhook calls (bad signature) are not stored anywhere, on
purpose - persisting a row per unauthenticated request would let anyone flood
the table. They only appear in the request log."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.audit_log import AuditLog
from app.models.enums import OrderStatus
from app.models.order_status_history import OrderStatusHistory
from app.services.integrations.health import integration_metrics
from app.services.integrations.telegram import notify_admin as telegram_notify_admin
from app.services.jobs import queue_stats
from app.services.notifications.email import EmailNotifier

logger = logging.getLogger("maru.tasks.check_alerts")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _recently_sent(db: Session, key: str, now: datetime) -> bool:
    cutoff = now - timedelta(minutes=settings.ALERT_COOLDOWN_MINUTES)
    return (
        db.execute(
            select(AuditLog.id)
            .where(AuditLog.action == "alert_sent", AuditLog.entity == "alert", AuditLog.entity_id == key, AuditLog.created_at >= cutoff)
            .limit(1)
        ).scalar_one_or_none()
        is not None
    )


def _send(db: Session, notifier, key: str, subject: str, body: str, now: datetime) -> bool:
    if _recently_sent(db, key, now):
        return False
    notifier.admin_alert(subject, body)
    db.add(AuditLog(user_id=None, action="alert_sent", entity="alert", entity_id=key, new_value=subject, created_at=now))
    db.commit()
    return True


def run_checks(db: Session, notifier=None, now: Optional[datetime] = None) -> list[str]:
    """Returns the alert keys that were sent."""
    if notifier is None:
        if not settings.ALERT_EMAIL:
            logger.warning("ALERT_EMAIL is not set; alerts are not being sent")
            return []
        notifier = EmailNotifier()
    now = now or _now()
    sent: list[str] = []

    def fire(key: str, subject: str, body: str) -> None:
        if _send(db, notifier, key, f"MARU alert: {subject}", body, now):
            sent.append(key)
            telegram_notify_admin(f"MARU alert: {subject}\n{body}")

    metrics = integration_metrics(db, now)
    for name, m in sorted(metrics.items()):
        if m["dead_letters"] > 0:
            fire(
                f"dead_letter:{name}",
                f"{name} has {m['dead_letters']} call(s) that exhausted their retries",
                "They need a manual retry from Admin > Integration Logs.",
            )
        lag = m["sync_lag_seconds"]
        if lag is not None and lag >= settings.ALERT_SYNC_LAG_MINUTES * 60:
            fire(
                f"sync_lag:{name}",
                f"{name} has been failing for {lag // 60} minutes",
                f"The oldest unresolved failure is {lag // 60} minutes old (threshold {settings.ALERT_SYNC_LAG_MINUTES}).",
            )

    backlog = sum(m["pending_retries"] for m in metrics.values())
    if backlog >= settings.ALERT_RETRY_BACKLOG:
        fire("retry_backlog", f"{backlog} integration calls are waiting for a retry", "Check the retry cron job and the connector.")

    jobs = queue_stats(db, now)
    if jobs["dead"] > 0:
        fire("jobs_dead", f"{jobs['dead']} background job(s) failed for good", "See Admin > Integration Logs > Background jobs and retry them.")
    if jobs["oldest_due_seconds"] is not None and jobs["oldest_due_seconds"] >= settings.ALERT_JOB_BACKLOG_MINUTES * 60:
        fire("jobs_backlog", f"Background jobs are waiting {jobs['oldest_due_seconds'] // 60} minutes", "Is the worker running? (python -m app.tasks.worker)")

    failures = db.execute(
        select(func.count(OrderStatusHistory.id)).where(
            OrderStatusHistory.to_status == OrderStatus.PAYMENT_FAILED,
            OrderStatusHistory.created_at >= now - timedelta(hours=1),
        )
    ).scalar_one()
    if failures >= settings.ALERT_PAYMENT_FAILURES:
        fire(
            "payment_failures",
            f"{failures} payment failures in the last hour",
            "Check the payment provider status and the webhook logs.",
        )
    return sent


if __name__ == "__main__":
    session = SessionLocal()
    try:
        keys = run_checks(session)
        print(f"alerts sent: {keys or 'none'}")
    finally:
        session.close()
