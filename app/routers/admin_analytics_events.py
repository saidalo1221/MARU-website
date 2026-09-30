from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.analytics_event import AnalyticsEvent
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.analytics_event import AnalyticsEventOut

router = APIRouter(prefix="/admin/analytics-events", tags=["admin-analytics-events"])


@router.get("/", response_model=list[AnalyticsEventOut])
def list_analytics_events(
    event_name: Optional[str] = None,
    user_id: Optional[int] = None,
    limit: int = 100,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> list[AnalyticsEvent]:
    limit = min(limit, 500)
    stmt = select(AnalyticsEvent).order_by(AnalyticsEvent.id.desc()).limit(limit)
    if event_name is not None:
        stmt = stmt.where(AnalyticsEvent.event_name == event_name)
    if user_id is not None:
        stmt = stmt.where(AnalyticsEvent.user_id == user_id)

    try:
        rows = db.execute(stmt).scalars().all()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch analytics events") from exc
    return list(rows)
