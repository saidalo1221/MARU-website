from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.integration_log import IntegrationLog, IntegrationLogStatus

DEFAULT_MAX_ATTEMPTS = 5


def _attempt_count(db: Session, integration: str, operation: str, internal_entity: str, internal_id: int) -> int:
    return db.execute(
        select(func.count(IntegrationLog.id)).where(
            IntegrationLog.integration == integration,
            IntegrationLog.operation == operation,
            IntegrationLog.internal_entity == internal_entity,
            IntegrationLog.internal_id == internal_id,
        )
    ).scalar_one()


def run_with_log(
    db: Session,
    integration: str,
    operation: str,
    internal_entity: str,
    internal_id: int,
    fn: Callable[[], bool],
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> bool:
    """Runs fn() -> bool (True = confirmed success) and records the outcome
    as an IntegrationLog row (PRD ТЗ№4 §57 — one row per attempt, append-only,
    like OrderStatusHistory). Never raises: an integration failure must not
    break the caller's request (PRD §78's isolation requirement) — the
    caller gets False back and the log row is the durable record that
    app/services/integrations/retry.py and the admin retry endpoint act on.

    Commits on its own; callers that are mid-transaction for unrelated work
    should call this only after their own commit, same as the existing
    fire-and-forget crm.push_order()/notifier calls it replaces."""
    attempt = _attempt_count(db, integration, operation, internal_entity, internal_id) + 1

    try:
        success = bool(fn())
        error_message = None if success else "Integration reported failure"
    except Exception as exc:  # noqa: BLE001 - deliberately broad: any connector bug must not propagate
        success = False
        error_message = str(exc)

    status = (
        IntegrationLogStatus.SUCCESS
        if success
        else (IntegrationLogStatus.DEAD_LETTER if attempt >= max_attempts else IntegrationLogStatus.FAILED)
    )
    db.add(
        IntegrationLog(
            integration=integration,
            operation=operation,
            internal_entity=internal_entity,
            internal_id=internal_id,
            status=status,
            error_message=error_message,
            attempt=attempt,
            completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
    )
    db.commit()
    return success
