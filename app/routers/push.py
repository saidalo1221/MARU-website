from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.dependencies import get_current_user_required
from app.models.push_subscription import PushSubscription
from app.models.user import User
from app.config import settings
from app.services import push

router = APIRouter(prefix="/push", tags=["push"], dependencies=[Depends(rate_limit("push", 60, 60))])


class Keys(BaseModel):
    p256dh: str = Field(min_length=10, max_length=255)
    auth: str = Field(min_length=6, max_length=100)


class SubscribeIn(BaseModel):
    endpoint: str = Field(min_length=10, max_length=500)
    keys: Keys


class UnsubscribeIn(BaseModel):
    endpoint: str = Field(min_length=10, max_length=500)


@router.get("/public-key")
def public_key() -> dict:
    """The key the browser needs to subscribe; `enabled` is false when the server has no VAPID keys."""
    return {"enabled": push.enabled(), "public_key": settings.VAPID_PUBLIC_KEY if push.enabled() else None}


@router.get("/status")
def my_status(user: User = Depends(get_current_user_required), db: Session = Depends(get_db)) -> dict:
    return {"enabled": push.enabled(), "devices": len(push.subscriptions_of(db, user.id))}


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
def subscribe(
    payload: SubscribeIn,
    user_agent: str = Header(default="", alias="User-Agent"),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> dict:
    if not push.enabled():
        raise HTTPException(status_code=503, detail="Push notifications are not configured")
    if urlparse(payload.endpoint).scheme != "https":
        raise HTTPException(status_code=400, detail="Invalid push endpoint")
    existing = db.execute(select(PushSubscription).where(PushSubscription.endpoint == payload.endpoint)).scalar_one_or_none()
    if existing is None:
        db.add(PushSubscription(user_id=user.id, endpoint=payload.endpoint, p256dh=payload.keys.p256dh, auth=payload.keys.auth, user_agent=user_agent[:200] or None))
    else:  # the same browser signed in as someone else, or refreshed its keys
        existing.user_id, existing.p256dh, existing.auth = user.id, payload.keys.p256dh, payload.keys.auth
    db.commit()
    return {"devices": len(push.subscriptions_of(db, user.id))}


@router.post("/unsubscribe")
def unsubscribe(payload: UnsubscribeIn, user: User = Depends(get_current_user_required), db: Session = Depends(get_db)) -> dict:
    db.execute(delete(PushSubscription).where(PushSubscription.endpoint == payload.endpoint, PushSubscription.user_id == user.id))
    db.commit()
    return {"devices": len(push.subscriptions_of(db, user.id))}
