from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.integration_log import IntegrationLog, IntegrationLogStatus
from app.models.user import User
from app.schemas.integration_log import IntegrationLogOut
from app.services.integrations.retry import UnknownIntegrationError, retry_one

router = APIRouter(prefix="/admin/integration-logs", tags=["admin-integration-logs"])


@router.get("/", response_model=list[IntegrationLogOut])
def list_integration_logs(
    status_filter: IntegrationLogStatus | None = None,
    integration: str | None = None,
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
) -> list[IntegrationLog]:
    stmt = select(IntegrationLog).order_by(IntegrationLog.id.desc())
    if status_filter is not None:
        stmt = stmt.where(IntegrationLog.status == status_filter)
    if integration is not None:
        stmt = stmt.where(IntegrationLog.integration == integration)
    return list(db.execute(stmt).scalars().all())


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
