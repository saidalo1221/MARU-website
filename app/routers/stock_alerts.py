from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.dependencies import get_current_user_optional
from app.models.sku import SKU
from app.models.stock_alert import StockAlert
from app.models.user import User
from app.services.order_service import available_stock

router = APIRouter(prefix="/stock-alerts", tags=["stock-alerts"])

Email = Annotated[
    str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
]


class StockAlertIn(BaseModel):
    sku_id: int
    # Optional for signed-in customers (their account email is used).
    email: Optional[Email] = None


class StockAlertOut(BaseModel):
    status: str = "ok"


@router.post(
    "/",
    response_model=StockAlertOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("stock_alert", 10, 60))],
)
def create_stock_alert(
    payload: StockAlertIn,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> StockAlertOut:
    email = payload.email or (user.email if user is not None else None)
    if not email:
        raise HTTPException(status_code=422, detail="email is required")

    sku = db.get(SKU, payload.sku_id)
    if sku is None or not sku.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")
    if available_stock(db, sku.id) > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This item is already in stock")

    try:
        alert = db.execute(select(StockAlert).where(StockAlert.sku_id == sku.id, StockAlert.email == email)).scalar_one_or_none()
        if alert is None:
            db.add(StockAlert(sku_id=sku.id, email=email, user_id=user.id if user is not None else None))
        else:
            alert.notified_at = None  # asking again re-arms the alert
        db.commit()
    except IntegrityError:
        db.rollback()  # a concurrent identical request created it first
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save alert") from exc
    return StockAlertOut()
