from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.shipping_rate import ANY, ShippingRate


class ShippingError(Exception):
    """Raised when no shipping rate (not even a wildcard fallback) is configured
    for a country/method. Routers translate this to a 4xx response."""


def cart_weight_g(cart: Cart) -> int:
    return sum((item.sku.unit_weight_g or 0) * item.quantity for item in cart.items)


def _find_rate(db: Session, country: str, delivery_method: str) -> ShippingRate | None:
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


def calculate_shipping(db: Session, country: str, delivery_method: str, weight_g: int) -> Decimal:
    rate = _find_rate(db, country, delivery_method)
    if rate is None:
        raise ShippingError(f"No shipping rate configured for {country} / {delivery_method}")

    weight_kg = Decimal(weight_g) / Decimal("1000")
    fee = rate.base_fee + rate.per_kg_fee * weight_kg
    return fee.quantize(Decimal("0.01"))
