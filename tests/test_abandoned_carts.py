"""PRD ТЗ№1 §39: one reminder e-mail per abandoned cart of a signed-in customer."""

from datetime import timedelta

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.user import User
from app.schemas.order import CheckoutRequest
from app.services.order_service import create_order
from app.tasks.abandoned_carts import _now, send_abandoned_cart_emails
from conftest import CHECKOUT_PAYLOAD, register


class _Mail:
    def __init__(self):
        self.sent = []

    def abandoned_cart(self, to_email, first_name, items, db=None):
        self.sent.append((to_email, items))


def _cart_for(db_session, email, sku, qty=2, age_hours=30, saved=False):
    user = db_session.query(User).filter_by(email=email).one()
    cart = Cart(user_id=user.id)
    db_session.add(cart)
    db_session.flush()
    item = CartItem(cart_id=cart.id, sku_id=sku.id, quantity=qty, saved_for_later=saved)
    db_session.add(item)
    db_session.commit()
    stamp = _now() - timedelta(hours=age_hours)
    cart.updated_at = stamp
    item.updated_at = stamp
    db_session.commit()
    return cart, user


def test_sends_once_after_the_idle_period(client, db_session, sku):
    register(client, "alice@example.com")
    cart, _ = _cart_for(db_session, "alice@example.com", sku, qty=3)
    mail = _Mail()
    assert send_abandoned_cart_emails(db_session, mail) == 1
    assert mail.sent == [("alice@example.com", [("Food Container", 3)])]
    assert send_abandoned_cart_emails(db_session, mail) == 0  # never twice for the same cart
    db_session.refresh(cart)
    assert cart.abandoned_email_sent_at is not None


def test_skips_fresh_stale_converted_ordered_saved_and_guest_carts(client, db_session, sku):
    for email in ("fresh", "stale", "ordered", "saved", "inactive"):
        register(client, f"{email}@example.com")
    _cart_for(db_session, "fresh@example.com", sku, age_hours=2)            # not idle long enough
    _cart_for(db_session, "stale@example.com", sku, age_hours=24 * 20)       # too old to nag about
    _cart_for(db_session, "saved@example.com", sku, saved=True)              # only "saved for later" lines
    c, u = _cart_for(db_session, "ordered@example.com", sku)
    order = create_order(db_session, c, CheckoutRequest(**CHECKOUT_PAYLOAD), u)  # converts the cart and orders
    db_session.commit()
    _, inactive = _cart_for(db_session, "inactive@example.com", sku)
    inactive.is_active = False
    db_session.commit()
    guest = Cart(token="guest-tok")
    db_session.add(guest)
    db_session.flush()
    item = CartItem(cart_id=guest.id, sku_id=sku.id, quantity=1)
    db_session.add(item)
    db_session.commit()
    item.updated_at = guest.updated_at = _now() - timedelta(hours=30)
    db_session.commit()

    mail = _Mail()
    assert send_abandoned_cart_emails(db_session, mail) == 0, mail.sent
    assert order.id


def test_a_new_order_after_the_cart_activity_cancels_the_reminder(client, db_session, sku):
    register(client, "alice@example.com")
    cart, user = _cart_for(db_session, "alice@example.com", sku, age_hours=30)
    other = Cart(user_id=None, token="x")
    db_session.add(other)
    db_session.flush()
    db_session.add(CartItem(cart_id=other.id, sku_id=sku.id, quantity=1))
    db_session.commit()
    create_order(db_session, other, CheckoutRequest(**CHECKOUT_PAYLOAD), user)  # bought elsewhere / on another device
    db_session.commit()
    assert send_abandoned_cart_emails(db_session, _Mail()) == 0


def test_email_text_and_failure_isolation(client, db_session, sku, monkeypatch):
    from app.services.notifications.email import EmailNotifier

    texts = []
    n = EmailNotifier()
    monkeypatch.setattr(n, "_send", lambda to, subject, body: texts.append((to, subject, body)))
    n.abandoned_cart("a@example.com", "Ali", [("Food Container", 2)], db=db_session)
    to, subject, body = texts[0]
    assert "cart" in subject.lower() and "Food Container x 2" in body and "/cart" in body and "Ali" in body

    register(client, "alice@example.com")
    cart, _ = _cart_for(db_session, "alice@example.com", sku)

    class Broken(_Mail):
        def abandoned_cart(self, *a, **k):
            raise RuntimeError("smtp down")

    assert send_abandoned_cart_emails(db_session, Broken()) == 0
    db_session.refresh(cart)
    assert cart.abandoned_email_sent_at is None  # will be retried on the next run
