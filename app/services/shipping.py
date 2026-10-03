from typing import Optional
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.services.currency import CurrencyError, convert_amount
from app.models.shipping_rate import ANY, ShippingRate


class ShippingError(Exception):
    """Raised when no shipping rate (not even a wildcard fallback) is configured
    for a country/method. Routers translate this to a 4xx response."""


def cart_weight_g(cart: Cart) -> int:
    return sum((item.sku.unit_weight_g or 0) * item.quantity for item in cart.items)


def _find_rate(db: Session, country: str, delivery_method: str) -> Optional[ShippingRate]:
    """Looks up the most specific configured rate first, falling back to
    wildcards so admins don't have to enumerate every country x method
    combination (PRD section 17)."""
    candidates = [
        (country, delivery_method),
        (country, ANY),
        (ANY, delivery_method),
        (ANY, ANY),
    ]
    for country_key, method_key in candidates:
        rate = db.execute(
            select(ShippingRate).where(
                ShippingRate.country == country_key,
                ShippingRate.delivery_method == method_key,
                ShippingRate.is_active.is_(True),
            )
        ).scalar_one_or_none()
        if rate is not None:
            return rate
    return None


def _threshold_in(db: Session, rate: ShippingRate, currency: str) -> Optional[Decimal]:
    if rate.free_shipping_threshold is None:
        return None
    try:
        return convert_amount(db, rate.free_shipping_threshold, rate.currency, currency)
    except CurrencyError:
        return None


def free_shipping_progress(
    db: Session, country: Optional[str], delivery_method: Optional[str], merchandise_total: Decimal, currency: str
) -> tuple[Optional[Decimal], Optional[Decimal]]:
    """(threshold, amount still needed) in `currency`, for a cart banner. With a
    known destination it uses that rate; otherwise the lowest offer anywhere,
    which is what a visitor can at best hope to unlock."""
    if country:
        rate = _find_rate(db, country, delivery_method or ANY)
        rates = [rate] if rate is not None else []
    else:
        rates = db.execute(
            select(ShippingRate).where(ShippingRate.is_active.is_(True), ShippingRate.free_shipping_threshold.is_not(None))
        ).scalars().all()
    thresholds = [t for t in (_threshold_in(db, r, currency) for r in rates) if t is not None]
    if not thresholds:
        return None, None
    threshold = min(thresholds)
    return threshold, max(Decimal("0.00"), threshold - merchandise_total)


def calculate_shipping(
    db: Session,
    country: str,
    delivery_method: str,
    weight_g: int,
    merchandise_total: Optional[Decimal] = None,
    currency: Optional[str] = None,
) -> Decimal:
    """`merchandise_total` (after discounts, in `currency`) enables the rate's
    free-shipping threshold; without it the fee is always charged."""
    rate = _find_rate(db, country, delivery_method)
    if rate is None:
        raise ShippingError(f"No shipping rate configured for {country} / {delivery_method}")

    if merchandise_total is not None and currency is not None:
        threshold = _threshold_in(db, rate, currency)
        if threshold is not None and merchandise_total >= threshold:
            return Decimal("0.00")

    weight_kg = Decimal(weight_g) / Decimal("1000")
    fee = rate.base_fee + rate.per_kg_fee * weight_kg
    return fee.quantize(Decimal("0.01"))
