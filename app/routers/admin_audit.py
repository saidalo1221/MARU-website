from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.audit_log import AuditLog
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.extras import AuditLogOut

router = APIRouter(prefix="/admin/audit-logs", tags=["admin-audit"])


@router.get("/", response_model=list[AuditLogOut])
def list_audit_logs(
    entity: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    user: User = Depends(require_role(UserRole.ACCOUNTANT)),
    db: Session = Depends(get_db),
) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    if entity:
        stmt = stmt.where(AuditLog.entity == entity)
    return list(db.execute(stmt).scalars().all())
