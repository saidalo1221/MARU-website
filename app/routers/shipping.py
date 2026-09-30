from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.models.shipping_rate import ANY, ShippingRate
from app.schemas.shipping import ShippingEstimateOut

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
def list_shipping_methods(country: Optional[str] = None, db: Session = Depends(get_db)) -> list[str]:
    """Delivery methods available for a country (or all configured methods if
    no country is given), for the checkout delivery-method picker."""
    stmt = select(ShippingRate.delivery_method).where(
        ShippingRate.is_active.is_(True), ShippingRate.delivery_method != ANY
    )
    if country is not None:
        stmt = stmt.where(ShippingRate.country.in_((country, ANY)))
    stmt = stmt.distinct().order_by(ShippingRate.delivery_method)
    return list(db.execute(stmt).scalars().all())


@router.get("/estimate", response_model=ShippingEstimateOut)
def shipping_estimate(country: Optional[str] = None, db: Session = Depends(get_db)) -> ShippingEstimateOut:
    """Fastest configured delivery window (and free-shipping offer) for a
    country, for the product page. Country-specific rates win over "*" ones;
    with no country it summarises every active rate."""
    stmt = select(ShippingRate).where(ShippingRate.is_active.is_(True), ShippingRate.max_delivery_days.is_not(None))
    rates = db.execute(stmt).scalars().all()
    if country:
        specific = [r for r in rates if r.country == country]
        rates = specific or [r for r in rates if r.country == ANY]
    if not rates:
        return ShippingEstimateOut()
    best = min(rates, key=lambda r: (r.max_delivery_days, r.min_delivery_days or 0))
    offers = [r for r in rates if r.free_shipping_threshold is not None and r.currency == best.currency]
    threshold = min((r.free_shipping_threshold for r in offers), default=None)
    return ShippingEstimateOut(
        min_days=best.min_delivery_days,
        max_days=best.max_delivery_days,
        free_shipping_threshold=threshold,
        currency=best.currency,
    )
