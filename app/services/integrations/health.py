"""Integration health numbers (PRD ТЗ№4 §65-66): which calls are still waiting
for a retry or a human, and how long they have been stuck. Shared by the admin
health endpoint and the alert task so both agree."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.integration_log import IntegrationLog, IntegrationLogStatus


@dataclass
class Unresolved:
    integration: str
    status: IntegrationLogStatus  # FAILED (retry pending) or DEAD_LETTER (needs a human)
    since: datetime  # first failed attempt after the last success


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def unresolved_calls(db: Session) -> list[Unresolved]:
    """Keys (integration, operation, entity, id) whose latest attempt is not a
    success. Python-side grouping, like integrations/retry.py: the table is
    small at PRD scale."""
    state: dict[tuple, dict] = {}
    rows = db.execute(
        select(
            IntegrationLog.integration,
            IntegrationLog.operation,
            IntegrationLog.internal_entity,
            IntegrationLog.internal_id,
            IntegrationLog.status,
            IntegrationLog.created_at,
        ).order_by(IntegrationLog.id)
    ).all()
    for integration, operation, entity, entity_id, status, created_at in rows:
        entry = state.setdefault((integration, operation, entity, entity_id), {"since": None})
        entry["integration"] = integration
        entry["status"] = status
        if status == IntegrationLogStatus.SUCCESS:
            entry["since"] = None
        elif entry["since"] is None:
            entry["since"] = created_at
    return [
        Unresolved(e["integration"], e["status"], e["since"])
        for e in state.values()
        if e["status"] != IntegrationLogStatus.SUCCESS
    ]


def integration_metrics(db: Session, now: Optional[datetime] = None, window: timedelta = timedelta(hours=24)) -> dict:
    """Per integration: avg/max call latency over the window, calls waiting for
    a retry, dead letters, and sync lag (age of the oldest unresolved failure,
    in seconds)."""
    now = now or _now()
    out: dict[str, dict] = {}

    def entry(name: str) -> dict:
        return out.setdefault(
            name,
            {"avg_latency_ms": None, "max_latency_ms": None, "pending_retries": 0, "dead_letters": 0, "sync_lag_seconds": None},
        )

    for name, avg, peak in db.execute(
        select(IntegrationLog.integration, func.avg(IntegrationLog.duration_ms), func.max(IntegrationLog.duration_ms))
        .where(IntegrationLog.created_at >= now - window, IntegrationLog.duration_ms.is_not(None))
        .group_by(IntegrationLog.integration)
    ).all():
        e = entry(name)
        e["avg_latency_ms"] = int(avg) if avg is not None else None
        e["max_latency_ms"] = peak

    for call in unresolved_calls(db):
        e = entry(call.integration)
        if call.status == IntegrationLogStatus.DEAD_LETTER:
            e["dead_letters"] += 1
        else:
            e["pending_retries"] += 1
        lag = max(0, int((now - call.since).total_seconds()))
        if e["sync_lag_seconds"] is None or lag > e["sync_lag_seconds"]:
            e["sync_lag_seconds"] = lag
    return out
