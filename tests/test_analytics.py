"""Server-side analytics event capture (PRD ТЗ№4 §46/§49)."""

from app.models.enums import OrderStatus, UserRole
from app.models.order import Order
from conftest import CHECKOUT_PAYLOAD, login, make_admin, register


def _event_names(client, headers):
    r = client.get("/api/v1/admin/analytics-events/", headers=headers)
    assert r.status_code == 200, r.text
    return [e["event_name"] for e in r.json()]


def test_signup_login_add_to_cart_begin_checkout_purchase_are_captured(client, sku, db_session):
    buyer_headers = register(client, "shopper@example.com")
    client.post("/api/v1/auth/login", json={"email": "shopper@example.com", "password": "Password123!"})
    client.post("/api/v1/cart/items", headers=buyer_headers, json={"sku_id": sku.id, "quantity": 1})
    r = client.post("/api/v1/orders/", headers=buyer_headers, json=CHECKOUT_PAYLOAD)
    assert r.status_code == 201, r.text
    order_id = r.json()["id"]

    from app.services.order_service import set_order_status

    order = db_session.get(Order, order_id)
    set_order_status(db_session, order, OrderStatus.PAID, None, note="test")

    make_admin(db_session, "marketing@example.com", UserRole.MARKETING_MANAGER)
    admin_headers = login(client, "marketing@example.com")
    names = _event_names(client, admin_headers)

    for expected in ("sign_up", "login", "add_to_cart", "begin_checkout", "purchase"):
        assert expected in names, f"{expected} missing from {names}"


def test_generate_lead_captured_on_quote_submission(client, db_session):
    client.post(
        "/api/v1/quotes/",
        json={"request_type": "quote", "name": "A", "country": "Uzbekistan", "email": "a@example.com"},
    )
    make_admin(db_session, "marketing2@example.com", UserRole.MARKETING_MANAGER)
    headers = login(client, "marketing2@example.com")
    assert "generate_lead" in _event_names(client, headers)


def test_add_to_wishlist_captured(client, sku, db_session):
    headers = register(client, "wisher@example.com")
    r = client.post(f"/api/v1/wishlist/{sku.id}", headers=headers)
    assert r.status_code == 201, r.text

    make_admin(db_session, "marketing3@example.com", UserRole.MARKETING_MANAGER)
    admin_headers = login(client, "marketing3@example.com")
    assert "add_to_wishlist" in _event_names(client, admin_headers)


def test_analytics_events_require_marketing_role(client):
    r = client.get("/api/v1/admin/analytics-events/")
    assert r.status_code == 401
