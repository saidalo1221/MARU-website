"""PRD ТЗ№1 §11 / §62: loyalty points - earning, spending, giving back, admin controls."""

from decimal import Decimal

import pytest

from app.models.enums import CustomerType, OrderStatus, UserRole
from app.models.loyalty import LoyaltyTransaction
from app.models.user import User
from app.schemas.order import CheckoutRequest
from app.services import loyalty
from app.services.order_service import OrderError, create_order, set_order_status
from conftest import CHECKOUT_PAYLOAD, login, make_admin, register
from test_orders_reservation import _cart_with


def _customer(client, db_session, email="alice@example.com"):
    register(client, email)
    return db_session.query(User).filter_by(email=email).one()


def _order(db_session, sku, user, qty=3, **over):
    order = create_order(db_session, _cart_with(db_session, sku, qty), CheckoutRequest(**{**CHECKOUT_PAYLOAD, **over}), user)
    db_session.commit()
    return order


def _grant(db_session, user, points):
    db_session.add(LoyaltyTransaction(user_id=user.id, kind="adjust", points=points, note="test"))
    db_session.commit()


def test_points_are_earned_when_an_order_is_paid_once(client, db_session, sku):
    user = _customer(client, db_session)
    order = _order(db_session, sku, user, qty=3)                       # 30 USD of goods
    assert loyalty.balance(db_session, user.id) == 0                   # nothing before payment
    set_order_status(db_session, order, OrderStatus.PAID, None)
    assert loyalty.balance(db_session, user.id) == 30                  # 1 point per USD
    set_order_status(db_session, order, OrderStatus.PROCESSING, None)
    assert loyalty.balance(db_session, user.id) == 30                  # later statuses do not pay again


def test_only_retail_accounts_earn_and_guests_have_no_points(client, db_session, sku):
    user = _customer(client, db_session)
    user.customer_type = CustomerType.WHOLESALE
    db_session.commit()
    set_order_status(db_session, _order(db_session, sku, user), OrderStatus.PAID, None)
    assert loyalty.balance(db_session, user.id) == 0
    guest = create_order(db_session, _cart_with(db_session, sku, 1), CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()
    set_order_status(db_session, guest, OrderStatus.PAID, None)  # no crash, nothing recorded
    assert db_session.query(LoyaltyTransaction).count() == 0


def test_spending_points_discounts_the_order_and_lowers_what_is_earned(client, db_session, sku):
    user = _customer(client, db_session)
    _grant(db_session, user, 1000)
    order = _order(db_session, sku, user, qty=4, loyalty_points=500)   # 40 USD goods, 500 pts = 5 USD
    assert order.loyalty_points_used == 500 and order.loyalty_discount_amount == Decimal("5.00")
    assert order.discount_amount == Decimal("5.00") and order.total_amount == order.subtotal_amount + order.delivery_amount + order.tax_amount - Decimal("5.00")
    assert sum(i.discount_amount for i in order.items) == Decimal("5.00")
    assert loyalty.balance(db_session, user.id) == 500                 # spent at once
    set_order_status(db_session, order, OrderStatus.PAID, None)
    assert loyalty.balance(db_session, user.id) == 500 + 35            # earned on the 35 USD actually paid


def test_limits_are_enforced(client, db_session, sku):
    user = _customer(client, db_session)
    _grant(db_session, user, 100)
    with pytest.raises(OrderError, match="at most 100"):
        create_order(db_session, _cart_with(db_session, sku, 3), CheckoutRequest(**{**CHECKOUT_PAYLOAD, "loyalty_points": 101}), user)  # balance 100
    db_session.rollback()
    _grant(db_session, user, 5000)
    with pytest.raises(OrderError, match="at most 1500"):                 # 50% of 30 USD = 15 USD = 1500 points
        create_order(db_session, _cart_with(db_session, sku, 3), CheckoutRequest(**{**CHECKOUT_PAYLOAD, "loyalty_points": 1501}), user)
    db_session.rollback()
    with pytest.raises(OrderError, match="sign in"):
        create_order(db_session, _cart_with(db_session, sku, 3), CheckoutRequest(**{**CHECKOUT_PAYLOAD, "loyalty_points": 10}), None)
    db_session.rollback()


def test_points_come_back_when_the_order_never_completes_and_after_a_refund(client, db_session, sku):
    user = _customer(client, db_session)
    _grant(db_session, user, 1000)
    unpaid = _order(db_session, sku, user, qty=2, loyalty_points=500)
    assert loyalty.balance(db_session, user.id) == 500
    set_order_status(db_session, unpaid, OrderStatus.CANCELLED, None)
    assert loyalty.balance(db_session, user.id) == 1000                # restored, once
    set_order_status(db_session, unpaid, OrderStatus.CANCELLED, None)
    assert loyalty.balance(db_session, user.id) == 1000

    paid = _order(db_session, sku, user, qty=2, loyalty_points=500)   # 20 USD goods, 5 USD off
    set_order_status(db_session, paid, OrderStatus.PAID, None)
    assert loyalty.balance(db_session, user.id) == 500 + 15
    set_order_status(db_session, paid, OrderStatus.REFUNDED, None)
    assert loyalty.balance(db_session, user.id) == 1000                # earn taken back, spent points returned


def test_api_summary_history_cart_preview_and_checkout(client, db_session, sku):
    user = _customer(client, db_session)
    _grant(db_session, user, 2000)
    h = login(client, "alice@example.com")
    me = client.get("/api/v1/loyalty/me", headers=h).json()
    assert me["enabled"] and me["eligible"] and me["balance"] == 2000 and me["history"][0]["kind"] == "adjust"

    client.post("/api/v1/cart/items", json={"sku_id": sku.id, "quantity": 4}, headers=h)
    cart = client.get("/api/v1/cart/?loyalty_points=700", headers=h).json()
    assert cart["loyalty"]["balance"] == 2000 and cart["loyalty"]["max_points"] == 2000 and cart["loyalty_points_applied"] == 700
    assert float(cart["loyalty_discount"]) == 7.0 and float(cart["discount"]) == 7.0 and float(cart["total"]) == 33.0
    assert client.get("/api/v1/cart/?loyalty_points=999999", headers=h).json()["loyalty_points_applied"] == 2000  # clamped in the preview

    r = client.post("/api/v1/orders/", json={**CHECKOUT_PAYLOAD, "loyalty_points": 700}, headers=h)
    assert r.status_code == 201, r.text
    assert r.json()["loyalty_points_used"] == 700 and float(r.json()["loyalty_discount_amount"]) == 7.0
    assert client.get("/api/v1/loyalty/me", headers=h).json()["balance"] == 1300
    bad = client.post("/api/v1/orders/", json={**CHECKOUT_PAYLOAD, "loyalty_points": 5}, headers=h)  # the cart is gone
    assert bad.status_code == 400


def test_guests_see_no_loyalty_block_in_the_cart(client, db_session, sku):
    r = client.get("/api/v1/cart/")
    tok = r.headers["X-Cart-Token"]
    client.post("/api/v1/cart/items", json={"sku_id": sku.id, "quantity": 1}, headers={"X-Cart-Token": tok})
    assert client.get("/api/v1/cart/?loyalty_points=50", headers={"X-Cart-Token": tok}).json()["loyalty"] is None


def test_admin_settings_and_adjustments(client, db_session, sku):
    user = _customer(client, db_session)
    make_admin(db_session, "mk@example.com", UserRole.MARKETING_MANAGER)
    ah = login(client, "mk@example.com")
    s = client.put("/api/v1/admin/loyalty/settings", json={"enabled": True, "earn_per_usd": "2", "point_value_usd": "0.02", "max_redeem_percent": 30}, headers=ah)
    assert s.status_code == 200 and client.get("/api/v1/admin/loyalty/settings", headers=ah).json()["earn_per_usd"] == "2.00"
    set_order_status(db_session, _order(db_session, sku, user, qty=1), OrderStatus.PAID, None)
    assert loyalty.balance(db_session, user.id) == 20                  # 10 USD x 2 points

    assert client.post("/api/v1/admin/loyalty/adjust", json={"user_id": user.id, "points": 100, "note": "welcome"}, headers=ah).status_code == 201
    assert client.post("/api/v1/admin/loyalty/adjust", json={"user_id": user.id, "points": -500, "note": "oops"}, headers=ah).status_code == 409  # never below zero
    assert client.get(f"/api/v1/admin/loyalty/users/{user.id}", headers=ah).json()["balance"] == 120

    client.put("/api/v1/admin/loyalty/settings", json={"enabled": False, "earn_per_usd": "2", "point_value_usd": "0.02", "max_redeem_percent": 30}, headers=ah)
    assert loyalty.max_points_for(db_session, user, Decimal("100"), "USD") == 0   # switched off
    assert client.get("/api/v1/loyalty/me", headers=login(client, "alice@example.com")).json()["enabled"] is False
    from app.models.audit_log import AuditLog
    assert db_session.query(AuditLog).filter(AuditLog.action.in_(["loyalty_settings_update", "loyalty_adjust"])).count() == 3


def test_split_adds_up_exactly():
    parts = loyalty.split(Decimal("0.07"), [Decimal("3.33"), Decimal("3.33"), Decimal("3.34"), Decimal("0")])
    assert sum(parts) == Decimal("0.07") and parts[3] == Decimal("0.00")
