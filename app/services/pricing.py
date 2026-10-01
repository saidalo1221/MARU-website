from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.category import Category
from app.models.order import Order
from app.models.enums import CustomerType, OrderStatus
from app.models.promo_code import PromoCode, PromoDiscountType, PromoRedemption
from app.models.quantity_price_tier import QuantityPriceTier
from app.models.sku import SKU
from app.services.currency import CurrencyError, convert_amount


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
    # A special price below retail is the SKU's sale price (it drives the "Sale"
    # badge and the struck-through old price in the storefront), so retail
    # customers pay it too; other customer types keep their own price column.
    if (
        customer_type == CustomerType.RETAIL
        and sku.special_price is not None
        and sku.special_price < base_price
    ):
        base_price = sku.special_price

    tier = db.execute(
        select(QuantityPriceTier)
        .where(QuantityPriceTier.sku_id == sku.id, QuantityPriceTier.min_quantity <= quantity)
        .order_by(QuantityPriceTier.min_quantity.desc())
    ).scalars().first()

    price = min(tier.price, base_price) if tier is not None else base_price
    return convert_amount(db, price, sku.currency, target_currency)


def _promo_amount(db: Session, amount: Decimal, promo: PromoCode, currency: Optional[str]) -> Decimal:
    """promo.min_order_amount and a FIXED discount_value are stated in
    promo.currency; convert them to the cart's currency. Unchanged when the
    promo has no currency or the cart has none to compare against."""
    if not promo.currency or not currency or promo.currency == currency:
        return amount
    try:
        return convert_amount(db, amount, promo.currency, currency)
    except CurrencyError as exc:
        raise PromoCodeError(str(exc)) from exc


def _category_family(db: Session, ids) -> set:
    """The given categories plus all their sub-categories."""
    family = set(ids)
    while True:
        children = set(db.execute(select(Category.id).where(Category.parent_id.in_(family))).scalars()) - family
        if not children:
            return family
        family |= children


def is_targeted(promo: PromoCode) -> bool:
    return bool(promo.product_ids or promo.category_ids)


def eligible_flags(db: Session, promo: PromoCode, lines: list) -> list:
    """For each (sku, line_total) line: does the promo discount apply to it? An untargeted promo
    applies to every line."""
    if not is_targeted(promo):
        return [True] * len(lines)
    products = set(promo.product_ids or [])
    categories = _category_family(db, promo.category_ids) if promo.category_ids else set()
    flags = []
    for sku, _total in lines:
        product = sku.variant.product
        flags.append(product.id in products or product.category_id in categories)
    return flags


def customer_uses(db: Session, promo_id: int, user_id: Optional[int], email: Optional[str]) -> int:
    """How many not-cancelled orders this customer already used the code on."""
    who = []
    if user_id is not None:
        who.append(PromoRedemption.user_id == user_id)
    if email:
        who.append(func.lower(PromoRedemption.email) == email.strip().lower())
    if not who:
        return 0
    return db.execute(
        select(func.count(PromoRedemption.id))
        .join(Order, Order.id == PromoRedemption.order_id)
        .where(PromoRedemption.promo_code_id == promo_id, or_(*who), Order.status.notin_((OrderStatus.CANCELLED, OrderStatus.PAYMENT_FAILED)))
    ).scalar_one()


def validate_promo(
    db: Session,
    code: str,
    subtotal: Decimal,
    currency: Optional[str] = None,
    lines: Optional[list] = None,
    user_id: Optional[int] = None,
    email: Optional[str] = None,
) -> PromoCode:
    """Read-only validation for cart-preview use. Does not lock the row or
    increment used_count — checkout redeems atomically (redeem_promo). `lines` is a list of
    (sku, line_total); with it a product/category-targeted code is checked against the cart and its
    minimum applies to the matching lines only."""
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
    if promo.max_uses_per_customer is not None and customer_uses(db, promo.id, user_id, email) >= promo.max_uses_per_customer:
        raise PromoCodeError("You have already used this promo code the maximum number of times")
    counted = subtotal
    if lines is not None and is_targeted(promo):
        flags = eligible_flags(db, promo, lines)
        if not any(flags):
            raise PromoCodeError("This promo code does not apply to the products in your cart")
        counted = sum((total for (_sku, total), ok in zip(lines, flags) if ok), Decimal("0"))
    minimum = _promo_amount(db, promo.min_order_amount, promo, currency)
    if counted < minimum:
        raise PromoCodeError(f"Order must be at least {minimum} to use this code")

    return promo


def apply_promo(
    subtotal: Decimal, promo: PromoCode, db: Optional[Session] = None, currency: Optional[str] = None
) -> Decimal:
    if promo.discount_type == PromoDiscountType.PERCENT:
        discount = subtotal * (promo.discount_value / Decimal("100"))
    elif db is not None:
        discount = _promo_amount(db, promo.discount_value, promo, currency)
    else:
        discount = promo.discount_value

    return max(Decimal("0"), min(discount, subtotal))


def promo_line_discounts(
    db: Session, promo: Optional[PromoCode], lines: list, currency: Optional[str] = None
) -> list:
    """Splits the promo discount over the cart lines: only matching lines are discounted, each in
    proportion to its value (the last matching line takes the rounding remainder), so the parts add up
    exactly to the total discount. `lines` is a list of (sku, line_total)."""
    zero = Decimal("0.00")
    if promo is None or not lines:
        return [zero] * len(lines)
    flags = eligible_flags(db, promo, lines)
    base = sum((total for (_sku, total), ok in zip(lines, flags) if ok), Decimal("0"))
    if base <= 0:
        return [zero] * len(lines)
    total_discount = apply_promo(base, promo, db, currency).quantize(Decimal("0.01"))
    out = [zero] * len(lines)
    matching = [i for i, ok in enumerate(flags) if ok]
    given = Decimal("0")
    for i in matching[:-1]:
        share = (total_discount * lines[i][1] / base).quantize(Decimal("0.01"))
        out[i] = share
        given += share
    out[matching[-1]] = total_discount - given
    return out


def record_redemption(db: Session, promo: PromoCode, order: Order, user_id: Optional[int], email: Optional[str]) -> None:
    db.add(PromoRedemption(promo_code_id=promo.id, order_id=order.id, user_id=user_id, email=(email or "").strip().lower() or None))


def redeem_promo(db: Session, promo: PromoCode) -> None:
    """Counts one use atomically. A plain `used_count += 1` after a read lets
    two concurrent checkouts both take the last use; this UPDATE only succeeds
    while the cap still has room."""
    result = db.execute(
        update(PromoCode)
        .where(PromoCode.id == promo.id, or_(PromoCode.max_uses.is_(None), PromoCode.used_count < PromoCode.max_uses))
        .values(used_count=PromoCode.used_count + 1)
    )
    if result.rowcount == 0:
        raise PromoCodeError("Promo code usage limit reached")
    db.refresh(promo)


def compute_cart_totals(
    db: Session,
    cart: Cart,
    customer_type: CustomerType,
    promo: Optional[PromoCode],
    delivery_amount: Decimal = Decimal("0"),
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """Returns (subtotal, discount, delivery, total). Formula per PRD section 8:
    Subtotal + Delivery - Discount = Total."""
    subtotal = Decimal("0")
    lines = []
    for item in cart.items:
        unit_price = resolve_unit_price(db, item.sku, customer_type, item.quantity, cart.currency)
        subtotal += unit_price * item.quantity
        lines.append((item.sku, unit_price * item.quantity))

    discount = sum(promo_line_discounts(db, promo, lines, cart.currency), Decimal("0"))
    total = subtotal + delivery_amount - discount

    return subtotal, discount, delivery_amount, total
