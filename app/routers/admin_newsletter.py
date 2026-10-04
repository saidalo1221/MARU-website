from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.newsletter_campaign import NewsletterCampaign
from app.models.newsletter_subscriber import NewsletterStatus, NewsletterSubscriber
from app.models.user import User
from app.services import campaigns
from app.services.audit import log_audit
from app.services.notifications.email import EmailNotifier

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


class CampaignIn(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=20000)
    locale: Optional[str] = Field(default=None, pattern="^(ru|uz|en)$")


class CampaignOut(BaseModel):
    id: int
    subject: str
    locale: Optional[str]
    recipients_total: int
    sent: int
    failed: int
    waiting: int
    created_at: datetime


def _campaign_out(db: Session, c: NewsletterCampaign) -> CampaignOut:
    p = campaigns.progress(db, c)
    return CampaignOut(id=c.id, subject=c.subject, locale=c.locale, recipients_total=c.recipients_total, created_at=c.created_at, **p)


@router.get("/campaigns", response_model=list[CampaignOut])
def list_campaigns(
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> list[CampaignOut]:
    rows = db.execute(select(NewsletterCampaign).order_by(NewsletterCampaign.id.desc()).limit(50)).scalars().all()
    return [_campaign_out(db, c) for c in rows]


@router.post("/campaigns/test")
def send_test(
    payload: CampaignIn,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
) -> dict:
    """Sends the draft to the admin's own address so they see it (and learn at once if SMTP is broken)."""
    try:
        EmailNotifier(raise_errors=True).custom(user.email, f"[TEST] {payload.subject}", payload.body + campaigns.footer("test"))
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"The mail server refused the message: {exc}")
    return {"sent_to": user.email}


@router.post("/campaigns", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
def send_campaign(
    payload: CampaignIn,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> CampaignOut:
    """Queues the mail for every CONFIRMED subscriber (optionally one language)."""
    campaign = campaigns.start_campaign(db, payload.subject, payload.body, payload.locale, user.id)
    log_audit(db, user, "newsletter_campaign", "newsletter_campaign", campaign.id, new={"subject": campaign.subject, "recipients": campaign.recipients_total})
    db.commit()
    return _campaign_out(db, campaign)
