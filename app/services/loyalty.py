"""Loyalty points (PRD ТЗ№1 §11 bonuses, §62 loyalty programme).

Rules (all adjustable in the admin panel except where noted):
- Only customer types the business ticked in Admin > Loyalty take part (retail by default; wholesale / distributor /
  export / special customers have their own price lists, so they are left out unless the business decides otherwise).
- Points are earned when an order is paid: floor(goods paid in USD x earn_per_usd x tier multiplier), where "goods paid" is the
  subtotal minus every discount (promo and points), without delivery or tax.
- Points can pay for part of an order at checkout: each point is worth `point_value_usd`, and at most
  `max_redeem_percent` of the goods (after promo discounts) can be paid that way. The discount is spread over the
  order lines like a promo discount, so tax and documents stay consistent.
- An order that never completes (cancelled or payment failed before being paid) gives the spent points back; a paid
  order that is refunded or cancelled loses the points it earned and gets the spent points back. Each of these happens
  at most once per order.
- Tiers (optional): the customer's tier is the highest one whose threshold their lifetime earned points reach.
- Expiry (optional): earned points left unspent after `expiry_days` are removed; the oldest points are spent first.
"""

from datetime import datetime, timedelta, timezone
from decimal import ROUND_DOWN, Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import OrderStatus
from app.models.loyalty import ADJUST, EARN, EARN_REVERSE, EXPIRE, REDEEM, REDEEM_RESTORE, LoyaltySettings, LoyaltyTier, LoyaltyTransaction
from app.models.user import User
from app.services.currency import CurrencyError, convert_amount

_PAID_OR_LATER = (
    OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.PACKED, OrderStatus.SHIPPED,
    OrderStatus.IN_TRANSIT, OrderStatus.DELIVERED, OrderStatus.RETURNED, OrderStatus.PARTIALLY_REFUNDED,
)


class LoyaltyError(Exception):
    """A points request that cannot be honoured; routers turn it into a 400."""


def get_settings(db: Session) -> LoyaltySettings:
    row = db.get(LoyaltySettings, 1)
    if row is None:
        row = LoyaltySettings(id=1, enabled=True, earn_per_usd=Decimal("1"), point_value_usd=Decimal("0.01"), max_redeem_percent=50)
        db.add(row)
        db.flush()
    return row


def eligible_types(settings: LoyaltySettings) -> set:
    return {t.strip() for t in (settings.eligible_customer_types or "").split(",") if t.strip()}


def takes_part(user: Optional[User], settings: LoyaltySettings) -> bool:
    return user is not None and user.customer_type.value in eligible_types(settings)


def lifetime_earned(db: Session, user_id: int) -> int:
    return int(db.execute(
        select(func.coalesce(func.sum(LoyaltyTransaction.points), 0)).where(LoyaltyTransaction.user_id == user_id, LoyaltyTransaction.kind.in_((EARN, EARN_REVERSE)))
    ).scalar_one())


def tiers(db: Session) -> list:
    return list(db.execute(select(LoyaltyTier).order_by(LoyaltyTier.min_points_earned)).scalars())


def tier_of(db: Session, user_id: int) -> Optional[LoyaltyTier]:
    earned = lifetime_earned(db, user_id)
    best = None
    for tier in tiers(db):
        if tier.min_points_earned <= earned:
            best = tier
    return best


def next_tier(db: Session, user_id: int) -> Optional[dict]:
    earned = lifetime_earned(db, user_id)
    for tier in tiers(db):
        if tier.min_points_earned > earned:
            return {"name": tier.name, "points_needed": tier.min_points_earned - earned, "earn_multiplier": float(tier.earn_multiplier)}
    return None


def expire_due(db: Session, user_id: int, now: Optional[datetime] = None) -> int:
    """Removes this customer's earned points that stayed unspent past `expiry_days` (oldest are spent first, so only
    what is genuinely left of an old batch expires). Returns the points expired; writes one `expire` row."""
    settings = get_settings(db)
    if not settings.expiry_days or settings.expiry_days <= 0:
        return 0
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now - timedelta(days=settings.expiry_days)
    rows = db.execute(select(LoyaltyTransaction).where(LoyaltyTransaction.user_id == user_id).order_by(LoyaltyTransaction.id)).scalars().all()
    lots = []  # [remaining points, created_at] of every batch that added points, oldest first
    for row in rows:
        if row.points > 0:
            lots.append([row.points, row.created_at])
        else:
            take = -row.points
            for lot in lots:
                used = min(lot[0], take)
                lot[0] -= used
                take -= used
                if take <= 0:
                    break
    expired = sum(lot[0] for lot in lots if lot[0] > 0 and lot[1] is not None and lot[1] <= cutoff)
    if expired > 0:
        db.add(LoyaltyTransaction(user_id=user_id, kind=EXPIRE, points=-expired, note=f"Unspent for more than {settings.expiry_days} days"))
        db.flush()
    return expired


def balance(db: Session, user_id: int) -> int:
    return int(db.execute(select(func.coalesce(func.sum(LoyaltyTransaction.points), 0)).where(LoyaltyTransaction.user_id == user_id)).scalar_one())


def point_value(db: Session, currency: str, settings: Optional[LoyaltySettings] = None) -> Decimal:
    """What one point is worth in `currency` (0 when no exchange rate exists)."""
    settings = settings or get_settings(db)
    try:
        return convert_amount(db, Decimal(str(settings.point_value_usd)), "USD", currency)
    except CurrencyError:
        return Decimal("0")


def max_points_for(db: Session, user: Optional[User], goods_net: Decimal, currency: str) -> int:
    """The most points this customer may spend on goods worth `goods_net` (after promo discounts)."""
    settings = get_settings(db)
    if not settings.enabled or not takes_part(user, settings) or goods_net <= 0:
        return 0
    expire_due(db, user.id)
    value = point_value(db, currency, settings)
    if value <= 0:
        return 0
    cap_amount = goods_net * Decimal(settings.max_redeem_percent) / Decimal(100)
    by_cap = int((cap_amount / value).to_integral_value(rounding=ROUND_DOWN))
    return max(0, min(by_cap, balance(db, user.id)))


def summary(db: Session, user: Optional[User], goods_net: Decimal, currency: str) -> Optional[dict]:
    """What the cart / checkout shows: None for guests and customers outside the programme."""
    settings = get_settings(db)
    if not settings.enabled or not takes_part(user, settings):
        return None
    expire_due(db, user.id)
    return {
        "balance": balance(db, user.id),
        "max_points": max_points_for(db, user, goods_net, currency),
        "point_value": float(point_value(db, currency, settings)),
        "earn_per_usd": float(settings.earn_per_usd),
    }


def spend_amount(db: Session, points: int, currency: str) -> Decimal:
    return (point_value(db, currency) * points).quantize(Decimal("0.01"))


def split(amount: Decimal, weights: list) -> list:
    """Spreads `amount` over weights in proportion; the last non-zero weight takes the rounding remainder."""
    zero = Decimal("0.00")
    total = sum(weights, Decimal("0"))
    out = [zero] * len(weights)
    if amount <= 0 or total <= 0:
        return out
    given = Decimal("0")
    last = max(i for i, w in enumerate(weights) if w > 0)
    for i, w in enumerate(weights):
        if w <= 0:
            continue
        share = (amount - given) if i == last else (amount * w / total).quantize(Decimal("0.01"))
        out[i] = share
        given += share
    return out


# ---- ledger writes (all inside the caller's transaction) ---------------------------------

def _add(db: Session, user_id: int, kind: str, points: int, order_id: Optional[int] = None, note: Optional[str] = None, by: Optional[int] = None) -> bool:
    """Adds a transaction; for order kinds returns False (and adds nothing) when it already exists."""
    if points == 0:
        return False
    if order_id is not None and db.execute(
        select(LoyaltyTransaction.id).where(LoyaltyTransaction.order_id == order_id, LoyaltyTransaction.kind == kind)
    ).first():
        return False
    try:
        with db.begin_nested():
            db.add(LoyaltyTransaction(user_id=user_id, kind=kind, points=points, order_id=order_id, note=note, created_by_user_id=by))
            db.flush()
    except IntegrityError:
        return False
    return True


def record_redeem(db: Session, user_id: int, order_id: int, points: int) -> None:
    _add(db, user_id, REDEEM, -points, order_id, "Points used at checkout")


def adjust(db: Session, user_id: int, points: int, note: str, admin_id: int) -> LoyaltyTransaction:
    if balance(db, user_id) + points < 0:
        raise LoyaltyError("The balance cannot go below zero")
    row = LoyaltyTransaction(user_id=user_id, kind=ADJUST, points=points, note=note[:300], created_by_user_id=admin_id)
    db.add(row)
    db.flush()
    return row


def _goods_paid_usd(db: Session, order) -> Decimal:
    goods = Decimal(str(order.subtotal_amount)) - Decimal(str(order.discount_amount))
    try:
        return convert_amount(db, goods, order.currency, "USD") if goods > 0 else Decimal("0")
    except CurrencyError:
        return Decimal("0")


def on_status_change(db: Session, order, old_status: OrderStatus, new_status: OrderStatus) -> None:
    """Called by set_order_status() after the order's status changed (inside its transaction)."""
    if order.user_id is None:
        return
    spent = int(getattr(order, "loyalty_points_used", 0) or 0)
    was_paid = old_status in _PAID_OR_LATER

    if new_status == OrderStatus.PAID and not was_paid:
        settings = get_settings(db)
        user = db.get(User, order.user_id)
        if settings.enabled and takes_part(user, settings):
            tier = tier_of(db, order.user_id)
            multiplier = Decimal(str(tier.earn_multiplier)) if tier is not None else Decimal("1")
            earned = int((_goods_paid_usd(db, order) * Decimal(str(settings.earn_per_usd)) * multiplier).to_integral_value(rounding=ROUND_DOWN))
            _add(db, order.user_id, EARN, earned, order.id, f"Order {order.order_number}")
    elif new_status in (OrderStatus.CANCELLED, OrderStatus.PAYMENT_FAILED) and not was_paid:
        _add(db, order.user_id, REDEEM_RESTORE, spent, order.id, f"Order {order.order_number} did not complete")
    elif new_status in (OrderStatus.CANCELLED, OrderStatus.REFUNDED) and was_paid:
        earned = db.execute(
            select(LoyaltyTransaction.points).where(LoyaltyTransaction.order_id == order.id, LoyaltyTransaction.kind == EARN)
        ).scalar_one_or_none()
        if earned:
            _add(db, order.user_id, EARN_REVERSE, -earned, order.id, f"Order {order.order_number} refunded")
        _add(db, order.user_id, REDEEM_RESTORE, spent, order.id, f"Order {order.order_number} refunded")


def history(db: Session, user_id: int, limit: int = 50) -> list:
    return list(db.execute(
        select(LoyaltyTransaction).where(LoyaltyTransaction.user_id == user_id).order_by(LoyaltyTransaction.id.desc()).limit(limit)
    ).scalars())
