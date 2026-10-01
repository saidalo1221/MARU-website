from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.integration_log import IntegrationLog, IntegrationLogStatus
from app.models.user import User
from app.schemas.integration_log import IntegrationHealthOut, IntegrationLogOut
from app.services.integrations.health import integration_metrics
from app.services.integrations.retry import UnknownIntegrationError, retry_one

router = APIRouter(prefix="/admin/integration-logs", tags=["admin-integration-logs"])


@router.get("/", response_model=list[IntegrationLogOut])
def list_integration_logs(
    status_filter: Optional[IntegrationLogStatus] = None,
    integration: Optional[str] = None,
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
) -> list[IntegrationLog]:
    stmt = select(IntegrationLog).order_by(IntegrationLog.id.desc())
    if status_filter is not None:
        stmt = stmt.where(IntegrationLog.status == status_filter)
    if integration is not None:
        stmt = stmt.where(IntegrationLog.integration == integration)
    return list(db.execute(stmt).scalars().all())


_HEALTH_WINDOW = timedelta(hours=24)


def _health_status(integration: str, success: int, failed: int, dead: int) -> str:
    """PRD ТЗ№4 §65. Over the last 24h: any dead letter, or only failures, is
    FAILED; some failures alongside successes is DEGRADED; no calls is
    HEALTHY unless the integration is not configured (DISABLED)."""
    if integration == "crm_bitrix24" and not settings.BITRIX24_WEBHOOK_URL:
        return "DISABLED"
    if dead or (failed and not success):
        return "FAILED"
    if failed:
        return "DEGRADED"
    return "HEALTHY"


@router.get("/health", response_model=list[IntegrationHealthOut])
def integration_health(
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
) -> list[IntegrationHealthOut]:
    since = datetime.now(timezone.utc).replace(tzinfo=None) - _HEALTH_WINDOW
    rows = db.execute(
        select(IntegrationLog.integration, IntegrationLog.status, func.count(), func.max(IntegrationLog.created_at))
        .where(IntegrationLog.created_at >= since)
        .group_by(IntegrationLog.integration, IntegrationLog.status)
    ).all()
    per: dict[str, dict] = {}
    for name, st, n, last in rows:
        entry = per.setdefault(name, {"success": 0, "failed": 0, "dead_letter": 0, "last": None})
        entry[st.value] = n
        if st == IntegrationLogStatus.SUCCESS and (entry["last"] is None or last > entry["last"]):
            entry["last"] = last
    # Known integrations show up even with no traffic yet.
    per.setdefault("crm_bitrix24", {"success": 0, "failed": 0, "dead_letter": 0, "last": None})
    metrics = integration_metrics(db)
    for name in metrics:
        per.setdefault(name, {"success": 0, "failed": 0, "dead_letter": 0, "last": None})
    return [
        IntegrationHealthOut(
            integration=name,
            status=_health_status(name, e["success"], e["failed"], e["dead_letter"]),
            success_24h=e["success"],
            failed_24h=e["failed"],
            dead_letter_24h=e["dead_letter"],
            last_success_at=e["last"],
            avg_latency_ms=metrics.get(name, {}).get("avg_latency_ms"),
            max_latency_ms=metrics.get(name, {}).get("max_latency_ms"),
            pending_retries=metrics.get(name, {}).get("pending_retries", 0),
            dead_letters_open=metrics.get(name, {}).get("dead_letters", 0),
            sync_lag_seconds=metrics.get(name, {}).get("sync_lag_seconds"),
        )
        for name, e in sorted(per.items())
    ]


@router.post("/{log_id}/retry", response_model=IntegrationLogOut)
def retry_integration_log(
    log_id: int,
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
) -> IntegrationLog:
    """PRD ТЗ№4 §54: after a DEAD_LETTER, an admin can manually retry. Also
    works on a plain FAILED row if you don't want to wait for the scheduled
    sweep (app/tasks/retry_integrations.py)."""
    row = db.get(IntegrationLog, log_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration log not found")

    try:
        retry_one(db, row.integration, row.operation, row.internal_entity, row.internal_id)
    except UnknownIntegrationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to retry integration") from exc

    latest = db.execute(
        select(IntegrationLog)
        .where(
            IntegrationLog.integration == row.integration,
            IntegrationLog.operation == row.operation,
            IntegrationLog.internal_entity == row.internal_entity,
            IntegrationLog.internal_id == row.internal_id,
        )
        .order_by(IntegrationLog.id.desc())
        .limit(1)
    ).scalar_one()
    return latest
