from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.models.shipping_rate import ANY, ShippingRate

router = APIRouter(prefix="/shipping", tags=["shipping"], dependencies=[Depends(rate_limit("shipping", 120, 60))])


@router.get("/countries", response_model=list[str])
def list_shipping_countries(db: Session = Depends(get_db)) -> list[str]:
    """Countries with a configured delivery rate, for a storefront country
    picker (PRD sections 17, 41)."""
    stmt = (
        select(ShippingRate.country)
        .where(ShippingRate.is_active.is_(True), ShippingRate.country != ANY)
        .distinct()
        .order_by(ShippingRate.country)
    )
    return list(db.execute(stmt).scalars().all())


@router.get("/methods", response_model=list[str])
def list_shipping_methods(country: str | None = None, db: Session = Depends(get_db)) -> list[str]:
    """Delivery methods available for a country (or all configured methods if
    no country is given), for the checkout delivery-method picker."""
    stmt = select(ShippingRate.delivery_method).where(
        ShippingRate.is_active.is_(True), ShippingRate.delivery_method != ANY
    )
    if country is not None:
        stmt = stmt.where(ShippingRate.country.in_((country, ANY)))
    stmt = stmt.distinct().order_by(ShippingRate.delivery_method)
    return list(db.execute(stmt).scalars().all())
