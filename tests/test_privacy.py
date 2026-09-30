"""Personal-data export and self-service account erasure."""

import json

from app.models.address import Address
from app.models.analytics_event import AnalyticsEvent
from app.models.cart import Cart
from app.models.enums import OrderStatus, UserRole
from app.models.newsletter_subscriber import NewsletterSubscriber
from app.models.order import Order
from app.models.stock_alert import StockAlert
from app.models.user import User
from app.models.wishlist_item import WishlistItem
from app.services.order_service import set_order_status
from conftest import CHECKOUT_PAYLOAD, login, make_admin, register

PASSWORD = "Password123!"


def _buyer_with_order(client, sku, db_session, email, final=OrderStatus.DELIVERED):
    headers = register(client, email)
    client.post("/api/v1/cart/items", headers=headers, json={"sku_id": sku.id, "quantity": 1})
    order = client.post("/api/v1/orders/", headers=headers, json=CHECKOUT_PAYLOAD).json()
    row = db_session.get(Order, order["id"])
    path = {
        OrderStatus.DELIVERED: [OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.PACKED, OrderStatus.SHIPPED, OrderStatus.DELIVERED],
        OrderStatus.PAID: [OrderStatus.PAID],
        OrderStatus.NEW: [],
    }[final]
    for step in path:
        set_order_status(db_session, row, step, None)
    return headers, order


def test_export_contains_my_data_and_no_secrets(client, sku, db_session):
    headers, order = _buyer_with_order(client, sku, db_session, "me@example.com")
    user = db_session.query(User).filter_by(email="me@example.com").one()
    db_session.add(Address(user_id=user.id, first_name="A", last_name="B", phone="1", country="UZ", city="T", address_line="St", postal_code="1"))
    db_session.add(WishlistItem(user_id=user.id, sku_id=sku.id))
    db_session.add(NewsletterSubscriber(email="me@example.com", token="secret-newsletter-token-000"))
    db_session.commit()

    r = client.get("/api/v1/privacy/export", headers=headers)
    assert r.status_code == 200
    assert "attachment" in r.headers["Content-Disposition"]
    data = json.loads(r.text)
    assert data["profile"]["email"] == "me@example.com"
    assert len(data["addresses"]) == 1 and len(data["wishlist"]) == 1
    assert data["orders"][0]["order_number"] == order["order_number"]
    assert data["orders"][0]["items"][0]["sku_code_snapshot"] == "SKU-1000-001"
    assert data["newsletter"][0]["email"] == "me@example.com"

    blob = r.text
    for secret in ("password_hash", "mfa_secret", "secret-newsletter-token-000", "guest_order_token", "payment_reference"):
        assert secret not in blob, secret


def test_export_only_contains_my_own_orders(client, sku, db_session):
    _buyer_with_order(client, sku, db_session, "a@example.com")
    headers_b, _ = _buyer_with_order(client, sku, db_session, "b@example.com")
    data = json.loads(client.get("/api/v1/privacy/export", headers=headers_b).text)
    assert len(data["orders"]) == 1 and data["orders"][0]["email"] == "alice@example.com"  # CHECKOUT_PAYLOAD email
    assert data["profile"]["email"] == "b@example.com"


def test_export_requires_login(client):
    assert client.get("/api/v1/privacy/export").status_code == 401


def test_erase_requires_password_confirmation_and_customer_role(client, db_session):
    headers = register(client, "eraseme@example.com")
    wrong = client.post("/api/v1/privacy/erase", headers=headers, json={"password": "nope", "confirm": "DELETE"})
    assert wrong.status_code == 403
    unconfirmed = client.post("/api/v1/privacy/erase", headers=headers, json={"password": PASSWORD, "confirm": "yes"})
    assert unconfirmed.status_code == 400
    assert db_session.query(User).filter_by(email="eraseme@example.com").one().is_active

    make_admin(db_session, "staff@example.com", UserRole.SALES_MANAGER)
    staff = login(client, "staff@example.com")
    assert client.post("/api/v1/privacy/erase", headers=staff, json={"password": PASSWORD, "confirm": "DELETE"}).status_code == 403


def test_erase_is_blocked_while_an_order_is_in_progress(client, sku, db_session):
    headers, _ = _buyer_with_order(client, sku, db_session, "busy@example.com", final=OrderStatus.PAID)
    r = client.post("/api/v1/privacy/erase", headers=headers, json={"password": PASSWORD, "confirm": "DELETE"})
    assert r.status_code == 409 and "in progress" in r.json()["detail"]
    assert db_session.query(User).filter_by(email="busy@example.com").one().is_active


def test_erase_anonymizes_account_deletes_personal_data_and_keeps_orders(client, sku, db_session):
    headers, order = _buyer_with_order(client, sku, db_session, "gone@example.com")
    user = db_session.query(User).filter_by(email="gone@example.com").one()
    user_id = user.id
    db_session.add(Address(user_id=user_id, first_name="A", last_name="B", phone="1", country="UZ", city="T", address_line="St", postal_code="1"))
    db_session.add(WishlistItem(user_id=user_id, sku_id=sku.id))
    db_session.add(NewsletterSubscriber(email="gone@example.com", token="tok-0123456789"))
    db_session.add(StockAlert(sku_id=sku.id, email="gone@example.com", user_id=user_id))
    db_session.add(AnalyticsEvent(event_name="view_item", user_id=user_id))
    user.first_name, user.phone = "Real", "+998901112233"
    db_session.commit()
    client.post("/api/v1/cart/items", headers=headers, json={"sku_id": sku.id, "quantity": 1})  # an open cart

    r = client.post("/api/v1/privacy/erase", headers=headers, json={"password": PASSWORD, "confirm": "DELETE"})
    assert r.status_code == 204, r.text

    db_session.expire_all()
    user = db_session.get(User, user_id)
    assert user.email == f"deleted-{user_id}@deleted.invalid"
    assert (user.first_name, user.last_name, user.phone) == (None, None, None)
    assert user.is_active is False

    assert db_session.query(Address).filter_by(user_id=user_id).count() == 0
    assert db_session.query(WishlistItem).filter_by(user_id=user_id).count() == 0
    assert db_session.query(NewsletterSubscriber).count() == 0
    assert db_session.query(StockAlert).count() == 0
    assert db_session.query(AnalyticsEvent).filter_by(user_id=user_id).count() == 0
    assert db_session.query(AnalyticsEvent).filter_by(event_name="view_item").count() == 1  # kept, unlinked
    assert db_session.query(Cart).filter_by(user_id=user_id).count() == 0

    kept = db_session.get(Order, order["id"])
    assert kept is not None and kept.order_number == order["order_number"]  # orders are retained


def test_erased_account_can_no_longer_log_in_or_use_old_token(client, sku, db_session):
    headers, _ = _buyer_with_order(client, sku, db_session, "locked@example.com")
    client.post("/api/v1/privacy/erase", headers=headers, json={"password": PASSWORD, "confirm": "DELETE"})
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    r = client.post("/api/v1/auth/login", json={"email": "locked@example.com", "password": PASSWORD, "device_id": "d"})
    assert r.status_code in (400, 401, 403)
