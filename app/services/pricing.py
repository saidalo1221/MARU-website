from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.enums import CustomerType
from app.models.promo_code import PromoCode, PromoDiscountType
from app.models.quantity_price_tier import QuantityPriceTier
from app.models.sku import SKU
from app.services.currency import convert_amount


class PromoCodeError(Exception):
    """Raised when a promo code can't be applied. Routers translate this to a 4xx response."""


def _now_naive_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def resolve_unit_price(
    db: Session, sku: SKU, customer_type: CustomerType, quantity: int, target_currency: str
) -> Decimal:
    """Base price is the customer-type tier column on SKU (falling back to retail).
    A matching quantity-break tier (PRD section 22) can only discount further, never
    raise the price above the customer's own negotiated rate (PRD section 53: quantity
    tiers are a "Quantity Discount" applied after "Customer Price", not a replacement).
    The result is converted from the SKU's own currency into target_currency
    (PRD section 14) — a no-op when they already match. May raise CurrencyError."""
    base_price = getattr(sku, f"{customer_type.value}_price", None) or sku.retail_price

    tier = db.execute(
        select(QuantityPriceTier)
        .where(QuantityPriceTier.sku_id == sku.id, QuantityPriceTier.min_quantity <= quantity)
        .order_by(QuantityPriceTier.min_quantity.desc())
    ).scalars().first()

    price = min(tier.price, base_price) if tier is not None else base_price
    return convert_amount(db, price, sku.currency, target_currency)


def validate_promo(db: Session, code: str, subtotal: Decimal) -> PromoCode:
    """Read-only validation for cart-preview use. Does not lock the row or
    increment used_count — checkout re-validates transactionally before redeeming."""
    promo = db.execute(select(PromoCode).where(PromoCode.code == code)).scalar_one_or_none()
    if promo is None or not promo.is_active:
        raise PromoCodeError("Promo code not found or inactive")

    now = _now_naive_utc()
    if promo.valid_from is not None and now < promo.valid_from:
        raise PromoCodeError("Promo code is not active yet")
    if promo.valid_until is not None and now > promo.valid_until:
        raise PromoCodeError("Promo code has expired")
    if promo.max_uses is not None and promo.used_count >= promo.max_uses:
        raise PromoCodeError("Promo code usage limit reached")
    if subtotal < promo.min_order_amount:
        raise PromoCodeError(f"Order must be at least {promo.min_order_amount} to use this code")

    return promo


def apply_promo(subtotal: Decimal, promo: PromoCode) -> Decimal:
    if promo.discount_type == PromoDiscountType.PERCENT:
        discount = subtotal * (promo.discount_value / Decimal("100"))
    else:
        discount = promo.discount_value

    return max(Decimal("0"), min(discount, subtotal))


def compute_cart_totals(
    db: Session,
    cart: Cart,
    customer_type: CustomerType,
    promo: PromoCode | None,
    delivery_amount: Decimal = Decimal("0"),
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """Returns (subtotal, discount, delivery, total). Formula per PRD section 8:
    Subtotal + Delivery - Discount = Total."""
    subtotal = Decimal("0")
    for item in cart.items:
        unit_price = resolve_unit_price(db, item.sku, customer_type, item.quantity, cart.currency)
        subtotal += unit_price * item.quantity

    discount = apply_promo(subtotal, promo) if promo is not None else Decimal("0")
    total = subtotal + delivery_amount - discount

    return subtotal, discount, delivery_amount, total
