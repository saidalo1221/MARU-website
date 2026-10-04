from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.marketing_spend import MarketingSpend
from app.models.user import User
from app.services.audit import log_audit
from app.services.dashboard import build_dashboard, month_start_of

router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])

_VIEWERS = (UserRole.SALES_MANAGER, UserRole.ACCOUNTANT, UserRole.MARKETING_MANAGER)


@router.get("/")
def dashboard(user: User = Depends(require_role(*_VIEWERS)), db: Session = Depends(get_db)) -> dict:
    """Sales, customer, marketing and funnel numbers (PRD ТЗ№1 §27-28, §59-60); see app/services/dashboard.py
    for exactly how each figure is defined."""
    return build_dashboard(db)


class SpendIn(BaseModel):
    month: date = Field(description="Any date in the month")
    channel: str = Field(min_length=1, max_length=60)
    amount_usd: Decimal = Field(gt=0, le=Decimal("100000000"))


class SpendOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    month: date
    channel: str
    amount_usd: Decimal


@router.get("/marketing-spend", response_model=list[SpendOut])
def list_spend(user: User = Depends(require_role(*_VIEWERS)), db: Session = Depends(get_db)) -> list[MarketingSpend]:
    return list(db.execute(select(MarketingSpend).order_by(MarketingSpend.month.desc(), MarketingSpend.id.desc()).limit(60)).scalars())


@router.post("/marketing-spend", response_model=SpendOut, status_code=status.HTTP_201_CREATED)
def add_spend(payload: SpendIn, user: User = Depends(require_role(UserRole.MARKETING_MANAGER, UserRole.ACCOUNTANT)), db: Session = Depends(get_db)) -> MarketingSpend:
    row = MarketingSpend(month=month_start_of(payload.month), channel=payload.channel.strip(), amount_usd=payload.amount_usd, created_by_user_id=user.id)
    db.add(row)
    db.flush()
    log_audit(db, user, "marketing_spend_add", "marketing_spend", row.id, new={"month": str(row.month), "channel": row.channel, "amount_usd": str(row.amount_usd)})
    db.commit()
    db.refresh(row)
    return row


@router.delete("/marketing-spend/{spend_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_spend(spend_id: int, user: User = Depends(require_role(UserRole.MARKETING_MANAGER, UserRole.ACCOUNTANT)), db: Session = Depends(get_db)) -> None:
    row: Optional[MarketingSpend] = db.get(MarketingSpend, spend_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    log_audit(db, user, "marketing_spend_delete", "marketing_spend", row.id, old={"month": str(row.month), "channel": row.channel, "amount_usd": str(row.amount_usd)})
    db.delete(row)
    db.commit()
