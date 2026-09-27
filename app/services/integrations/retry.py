from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.integration_log import IntegrationLog, IntegrationLogStatus
from app.models.order import Order
from app.models.quote_request import QuoteRequest
from app.services.crm.bitrix24 import Bitrix24Connector
from app.services.integrations.log import DEFAULT_MAX_ATTEMPTS, run_with_log

_crm = Bitrix24Connector()

# Add an entry here for every (integration, operation) pushed through
# run_with_log(), so both the scheduled sweep and the manual admin retry
# endpoint know how to re-run it. Keyed by string, not a live callable,
# because IntegrationLog only stores strings (PRD §57's field list).
_DISPATCH: dict[tuple[str, str], "callable"] = {
    ("crm_bitrix24", "push_order"): lambda db, internal_id: _crm.push_order(db.get(Order, internal_id)),
    ("crm_bitrix24", "push_quote"): lambda db, internal_id: _crm.push_quote(db.get(QuoteRequest, internal_id)),
}


class UnknownIntegrationError(Exception):
    """Raised when a log row names an (integration, operation) with no
    registered dispatch entry — nothing to retry it with."""


def retry_one(db: Session, integration: str, operation: str, internal_entity: str, internal_id: int) -> bool:
    dispatch = _DISPATCH.get((integration, operation))
    if dispatch is None:
        raise UnknownIntegrationError(f"No retry handler registered for {integration}/{operation}")
    return run_with_log(
        db, integration, operation, internal_entity, internal_id, lambda: dispatch(db, internal_id)
    )


def _latest_rows(db: Session) -> list[IntegrationLog]:
    """The most recent row per (integration, operation, internal_entity,
    internal_id) group — later rows for the same key overwrite earlier ones
    since IntegrationLog.id is inserted in order. Small-table Python-side
    grouping is simplest here (PRD-scale data, not big-data) rather than a
    window-function query."""
    rows = db.execute(select(IntegrationLog).order_by(IntegrationLog.id)).scalars().all()
    latest: dict[tuple[str, str, str, int], IntegrationLog] = {}
    for row in rows:
        latest[(row.integration, row.operation, row.internal_entity, row.internal_id)] = row
    return list(latest.values())


def retry_failed_integrations(db: Session, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> int:
    """Retries every integration whose most recent attempt is FAILED (not yet
    DEAD_LETTER — those need a human, via the admin retry endpoint). Meant to
    be scheduled externally (cron/systemd timer), same as
    app/tasks/expire_reservations.py — this project has no task queue yet."""
    retried = 0
    for row in _latest_rows(db):
        if row.status != IntegrationLogStatus.FAILED:
            continue
        if (row.integration, row.operation) not in _DISPATCH:
            continue
        retry_one(db, row.integration, row.operation, row.internal_entity, row.internal_id)
        retried += 1
    return retried
