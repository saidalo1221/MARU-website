from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.shipping_rate import ShippingRate
from app.models.user import User
from app.services.audit import audit_create, audit_update, log_audit
from app.schemas.shipping import ShippingRateCreate, ShippingRateOut, ShippingRateUpdate

# Delivery cost isn't assigned to a specific role in PRD section 34; it's gated
# to Sales Manager since shipping cost is resolved as part of order fulfillment
# ("Заказы и клиенты"), which they already own.
router = APIRouter(prefix="/admin/shipping-rates", tags=["admin-shipping-rates"])


@router.get("/", response_model=list[ShippingRateOut])
def list_shipping_rates(
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
) -> list[ShippingRate]:
    try:
        rates = db.execute(select(ShippingRate).order_by(ShippingRate.id)).scalars().all()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch shipping rates") from exc

    return list(rates)


@router.post("/", response_model=ShippingRateOut, status_code=status.HTTP_201_CREATED)
def create_shipping_rate(
    payload: ShippingRateCreate,
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
) -> ShippingRate:
    rate = ShippingRate(**payload.model_dump())
    db.add(rate)
    try:
        audit_create(db, user, "shipping_rate_create", "shipping_rate", rate, payload.model_dump())
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A rate for this country/delivery method already exists",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create shipping rate") from exc

    db.refresh(rate)
    return rate


@router.patch("/{rate_id}", response_model=ShippingRateOut)
def update_shipping_rate(
    rate_id: int,
    payload: ShippingRateUpdate,
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
) -> ShippingRate:
    try:
        rate = db.get(ShippingRate, rate_id)
        if rate is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipping rate not found")

        changes = payload.model_dump(exclude_unset=True)
        audit_update(db, user, "shipping_rate_update", "shipping_rate", rate, changes)
        for field, value in changes.items():
            setattr(rate, field, value)

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update shipping rate") from exc

    db.refresh(rate)
    return rate
