"""Reminds signed-in customers about a cart they left behind (PRD ТЗ№1 §39). One e-mail per cart, sent
when the cart has been untouched for ABANDONED_CART_HOURS (and not longer than ABANDONED_CART_MAX_AGE_DAYS),
the customer has not ordered since, and the account is active. Guests are not reminded: the platform has no
e-mail for them until checkout. Push notifications and ad remarketing are not part of this task (they need
a push service / ad-platform audiences). Schedule it hourly:

    python -m app.tasks.abandoned_carts
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.order import Order
from app.models.user import User
from app.services import push
from app.services.notifications.email import EmailNotifier


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def send_abandoned_cart_emails(db: Session, notifier=None, now: Optional[datetime] = None) -> int:
    """Returns how many reminders were sent; commits per cart so one failure cannot repeat or block the rest."""
    notifier = notifier or EmailNotifier()
    now = now or _now()
    idle_before = now - timedelta(hours=settings.ABANDONED_CART_HOURS)
    too_old = now - timedelta(days=settings.ABANDONED_CART_MAX_AGE_DAYS)

    last_touch = func.max(CartItem.updated_at)
    rows = db.execute(
        select(Cart, last_touch)
        .join(CartItem, CartItem.cart_id == Cart.id)
        .where(
            Cart.is_active.is_(True),
            Cart.user_id.is_not(None),
            Cart.converted_at.is_(None),
            Cart.abandoned_email_sent_at.is_(None),
            CartItem.saved_for_later.is_(False),
        )
        .group_by(Cart.id)
    ).all()

    sent = 0
    for cart, touched in rows:
        activity = max(t for t in (touched, cart.updated_at) if t is not None)
        if not (too_old <= activity <= idle_before):
            continue
        user = db.get(User, cart.user_id)
        if user is None or not user.is_active or not user.email:
            continue
        ordered_since = db.execute(
            select(func.count(Order.id)).where(Order.user_id == user.id, Order.created_at >= activity)
        ).scalar_one()
        if ordered_since:
            continue
        items = [(i.sku.variant.product.name, i.quantity) for i in cart.items if not i.saved_for_later]
        if not items:
            continue
        try:
            notifier.abandoned_cart(user.email, user.first_name, items, db=db)
            push.notify_user(db, user.id, "MARU", "You left something in your cart.", "/cart")
            cart.abandoned_email_sent_at = now
            db.commit()
            sent += 1
        except Exception:  # noqa: BLE001
            db.rollback()
    return sent


if __name__ == "__main__":
    session = SessionLocal()
    try:
        print(f"abandoned-cart emails sent: {send_abandoned_cart_emails(session)}")
    finally:
        session.close()
