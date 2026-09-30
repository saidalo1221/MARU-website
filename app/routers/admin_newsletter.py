from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.newsletter_subscriber import NewsletterStatus, NewsletterSubscriber
from app.models.user import User

router = APIRouter(prefix="/admin/newsletter", tags=["admin-newsletter"])


class SubscriberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    locale: str
    status: NewsletterStatus
    created_at: datetime
    confirmed_at: Optional[datetime]
    unsubscribed_at: Optional[datetime]


class SubscriberListOut(BaseModel):
    counts: dict[str, int]
    subscribers: list[SubscriberOut]


@router.get("/", response_model=SubscriberListOut)
def list_subscribers(
    status_filter: Optional[NewsletterStatus] = None,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> SubscriberListOut:
    stmt = select(NewsletterSubscriber).order_by(NewsletterSubscriber.id.desc()).limit(1000)
    if status_filter is not None:
        stmt = stmt.where(NewsletterSubscriber.status == status_filter)
    rows = db.execute(stmt).scalars().all()
    totals = db.execute(select(NewsletterSubscriber.status, func.count()).group_by(NewsletterSubscriber.status)).all()
    return SubscriberListOut(counts={s.value: n for s, n in totals}, subscribers=list(rows))
