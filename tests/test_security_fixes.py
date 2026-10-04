"""Regression tests for the pre-launch security review: registration cannot pick a price list, a cancelled or
refunded order cannot be confirmed as paid again, and the public analytics endpoint cannot skip the consent check."""
from app.models.enums import CustomerType, OrderStatus
from app.models.order import Order
from app.models.user import User
from conftest import CHECKOUT_PAYLOAD, register


def test_registration_ignores_a_requested_customer_type(client, db_session):
    r = client.post("/api/v1/auth/register", json={
        "email": "sneaky@example.com", "password": "Password123!", "customer_type": "distributor"})
    assert r.status_code == 201, r.text
    user = db_session.query(User).filter(User.email == "sneaky@example.com").one()
    assert user.customer_type == CustomerType.RETAIL


class _FakeStripe:
    """Stripe keeps reporting "succeeded" for a payment that was later refunded or cancelled."""

    def create_intent(self, order):
        return "pi_test"

    def confirm(self, reference):
        return True


def _order(client, sku):
    headers = register(client, f"payer{id(object())}@example.com")
    client.post("/api/v1/cart/items", headers=headers, json={"sku_id": sku.id, "quantity": 1})
    r = client.post("/api/v1/orders/", headers=headers, json={**CHECKOUT_PAYLOAD, "payment_method": "payme"})
    assert r.status_code == 201, r.text
    return r.json()["id"], headers


def test_confirm_payment_only_works_while_the_order_is_waiting_for_payment(client, sku, db_session, monkeypatch):
    monkeypatch.setattr("app.routers.orders.get_payment_gateway", lambda method: _FakeStripe())
    order_id, headers = _order(client, sku)
    url = f"/api/v1/orders/{order_id}/confirm-payment"

    # cancelled and refunded orders stay as they are
    for blocked in (OrderStatus.CANCELLED, OrderStatus.REFUNDED, OrderStatus.RETURNED):
        row = db_session.get(Order, order_id)
        row.status = blocked
        db_session.commit()
        assert client.post(url, headers=headers).status_code == 409
        db_session.refresh(row)
        assert row.status == blocked

    # a waiting order is confirmed ...
    row = db_session.get(Order, order_id)
    row.status = OrderStatus.PAYMENT_PENDING
    db_session.commit()
    assert client.post(url, headers=headers).status_code == 200
    db_session.refresh(row)
    assert row.status == OrderStatus.PAID

    # ... and asking again (the storefront polls) changes nothing, also once fulfilment has moved on
    assert client.post(url, headers=headers).status_code == 200
    row.status = OrderStatus.SHIPPED
    db_session.commit()
    assert client.post(url, headers=headers).status_code == 200
    db_session.refresh(row)
    assert row.status == OrderStatus.SHIPPED


def test_analytics_properties_cannot_set_record_event_parameters(client):
    for key in ("forward_ads", "db", "user", "session_id", "event_name"):
        r = client.post("/api/v1/analytics/events", json={"event_name": "search", "properties": {key: True}})
        assert r.status_code == 422, key
    ok = client.post("/api/v1/analytics/events", json={"event_name": "search", "properties": {"search_string": "box"}})
    assert ok.status_code == 204


def test_customers_cancel_unpaid_orders_only(client, sku, db_session):
    order_id, headers = _order(client, sku)
    row = db_session.get(Order, order_id)
    url = f"/api/v1/orders/{order_id}/cancel"

    # once paid (or further along) the order is cancelled and refunded by staff, not online
    for paid in (OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.SHIPPED):
        row.status = paid
        db_session.commit()
        r = client.post(url, headers=headers)
        assert r.status_code == 400 and "contact us" in r.text.lower()
        db_session.refresh(row)
        assert row.status == paid

    # an unpaid order can still be cancelled
    row.status = OrderStatus.PAYMENT_PENDING
    db_session.commit()
    assert client.post(url, headers=headers).status_code == 200
    db_session.refresh(row)
    assert row.status == OrderStatus.CANCELLED


def test_a_refunded_order_stays_refunded(client, sku, db_session):
    from app.services.order_service import set_order_status

    order_id, _ = _order(client, sku)
    row = db_session.get(Order, order_id)
    row.status = OrderStatus.REFUNDED
    db_session.commit()
    for later in (OrderStatus.PAID, OrderStatus.PAYMENT_PENDING, OrderStatus.CANCELLED):
        set_order_status(db_session, row, later, None, note="late callback")
        db_session.refresh(row)
        assert row.status == OrderStatus.REFUNDED
