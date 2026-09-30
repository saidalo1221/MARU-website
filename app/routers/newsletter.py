from datetime import datetime, timezone
from secrets import token_urlsafe
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.models.newsletter_subscriber import NewsletterStatus, NewsletterSubscriber
from app.services.notifications.email import EmailNotifier

router = APIRouter(prefix="/newsletter", tags=["newsletter"])
notifier = EmailNotifier()

Email = Annotated[
    str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
]


class SubscribeIn(BaseModel):
    email: Email
    locale: Optional[str] = None


class TokenIn(BaseModel):
    token: Annotated[str, StringConstraints(min_length=10, max_length=64)]


class OkOut(BaseModel):
    status: str = "ok"


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _by_token(db: Session, token: str) -> NewsletterSubscriber:
    row = db.execute(select(NewsletterSubscriber).where(NewsletterSubscriber.token == token)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired link")
    return row


@router.post(
    "/subscribe",
    response_model=OkOut,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit("newsletter_subscribe", 5, 60))],
)
def subscribe(payload: SubscribeIn, db: Session = Depends(get_db)) -> OkOut:
    """Always answers the same way, so the form can't be used to find out
    whether an address is already on the list."""
    locale = payload.locale if payload.locale in ("en", "ru", "uz") else "en"
    row = db.execute(select(NewsletterSubscriber).where(NewsletterSubscriber.email == payload.email)).scalar_one_or_none()
    try:
        if row is None:
            row = NewsletterSubscriber(email=payload.email, locale=locale, token=token_urlsafe(32))
            db.add(row)
        elif row.status == NewsletterStatus.CONFIRMED:
            return OkOut()  # already subscribed: send nothing
        else:
            row.status = NewsletterStatus.PENDING
            row.locale = locale
        db.commit()
    except IntegrityError:
        db.rollback()  # a concurrent identical signup won; it already sent the email
        return OkOut()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to subscribe") from exc

    notifier.newsletter_confirmation(row.email, row.token, db=db)
    return OkOut()


@router.post("/confirm", response_model=OkOut, dependencies=[Depends(rate_limit("newsletter_token", 20, 60))])
def confirm(payload: TokenIn, db: Session = Depends(get_db)) -> OkOut:
    row = _by_token(db, payload.token)
    if row.status != NewsletterStatus.CONFIRMED:
        row.status = NewsletterStatus.CONFIRMED
        row.confirmed_at = _now()
        row.unsubscribed_at = None
        db.commit()
    return OkOut()


@router.post("/unsubscribe", response_model=OkOut, dependencies=[Depends(rate_limit("newsletter_token", 20, 60))])
def unsubscribe(payload: TokenIn, db: Session = Depends(get_db)) -> OkOut:
    row = _by_token(db, payload.token)
    if row.status != NewsletterStatus.UNSUBSCRIBED:
        row.status = NewsletterStatus.UNSUBSCRIBED
        row.unsubscribed_at = _now()
        db.commit()
    return OkOut()
