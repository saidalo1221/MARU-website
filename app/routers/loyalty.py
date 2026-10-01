from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.dependencies import get_current_user_required, require_role
from app.models.enums import UserRole
from app.models.user import User
from app.services import loyalty
from app.services.audit import log_audit

router = APIRouter(prefix="/loyalty", tags=["loyalty"], dependencies=[Depends(rate_limit("loyalty", 60, 60))])
admin_router = APIRouter(prefix="/admin/loyalty", tags=["admin-loyalty"])


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    points: int
    order_id: Optional[int]
    note: Optional[str]
    created_at: datetime


class MyLoyaltyOut(BaseModel):
    enabled: bool
    eligible: bool  # false for wholesale / distributor / export / special customers
    balance: int
    value_usd: float  # what one point is worth in USD
    earn_per_usd: float
    max_redeem_percent: int
    history: list[TransactionOut]


@router.get("/me", response_model=MyLoyaltyOut)
def my_loyalty(user: User = Depends(get_current_user_required), db: Session = Depends(get_db)) -> dict:
    settings = loyalty.get_settings(db)
    db.commit()
    return {
        "enabled": bool(settings.enabled),
        "eligible": loyalty.takes_part(user),
        "balance": loyalty.balance(db, user.id),
        "value_usd": float(settings.point_value_usd),
        "earn_per_usd": float(settings.earn_per_usd),
        "max_redeem_percent": settings.max_redeem_percent,
        "history": loyalty.history(db, user.id),
    }


# ---------------------------------------------------------------- admin

class SettingsIn(BaseModel):
    enabled: bool
    earn_per_usd: Decimal = Field(ge=0, le=1000)
    point_value_usd: Decimal = Field(ge=0, le=100)
    max_redeem_percent: int = Field(ge=0, le=100)


class SettingsOut(SettingsIn):
    model_config = ConfigDict(from_attributes=True)


class AdjustIn(BaseModel):
    user_id: int
    points: int = Field(ge=-1_000_000, le=1_000_000)
    note: str = Field(min_length=1, max_length=300)


@admin_router.get("/settings", response_model=SettingsOut)
def get_settings(user: User = Depends(require_role(UserRole.MARKETING_MANAGER, UserRole.SALES_MANAGER)), db: Session = Depends(get_db)):
    row = loyalty.get_settings(db)
    db.commit()
    return row


@admin_router.put("/settings", response_model=SettingsOut)
def update_settings(payload: SettingsIn, user: User = Depends(require_role(UserRole.MARKETING_MANAGER)), db: Session = Depends(get_db)):
    row = loyalty.get_settings(db)
    old = {"enabled": row.enabled, "earn_per_usd": str(row.earn_per_usd), "point_value_usd": str(row.point_value_usd), "max_redeem_percent": row.max_redeem_percent}
    row.enabled = payload.enabled
    row.earn_per_usd = payload.earn_per_usd
    row.point_value_usd = payload.point_value_usd
    row.max_redeem_percent = payload.max_redeem_percent
    log_audit(db, user, "loyalty_settings_update", "loyalty_settings", 1, old, payload.model_dump(mode="json"))
    db.commit()
    db.refresh(row)
    return row


@admin_router.get("/users/{user_id}", response_model=MyLoyaltyOut)
def user_loyalty(user_id: int, user: User = Depends(require_role(UserRole.SALES_MANAGER, UserRole.MARKETING_MANAGER)), db: Session = Depends(get_db)) -> dict:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    settings = loyalty.get_settings(db)
    return {
        "enabled": bool(settings.enabled), "eligible": loyalty.takes_part(target), "balance": loyalty.balance(db, user_id),
        "value_usd": float(settings.point_value_usd), "earn_per_usd": float(settings.earn_per_usd),
        "max_redeem_percent": settings.max_redeem_percent, "history": loyalty.history(db, user_id, 100),
    }


@admin_router.post("/adjust", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def adjust_points(payload: AdjustIn, user: User = Depends(require_role(UserRole.SALES_MANAGER, UserRole.MARKETING_MANAGER)), db: Session = Depends(get_db)):
    target = db.get(User, payload.user_id)
    if target is None or target.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=404, detail="Customer not found")
    try:
        row = loyalty.adjust(db, target.id, payload.points, payload.note, user.id)
    except loyalty.LoyaltyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    log_audit(db, user, "loyalty_adjust", "user", target.id, new={"points": payload.points, "note": payload.note})
    db.commit()
    db.refresh(row)
    return row
