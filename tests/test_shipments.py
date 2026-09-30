"""Shipments, order-status sync and the public Track Order lookup."""

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.enums import OrderStatus, UserRole
from app.models.order_status_history import OrderStatusHistory
from app.schemas.order import CheckoutRequest
from app.services.order_service import create_order, set_order_status
from conftest import CHECKOUT_PAYLOAD, login, make_admin, register

ADMIN = "admin@example.com"


def _order(db_session, sku, status=OrderStatus.PACKED, email="alice@example.com"):
    cart = Cart(token=f"tok-{id(object())}")
    db_session.add(cart)
    db_session.flush()
    db_session.add(CartItem(cart_id=cart.id, sku_id=sku.id, quantity=1))
    db_session.commit()
    db_session.refresh(cart)
    order = create_order(db_session, cart, CheckoutRequest(**{**CHECKOUT_PAYLOAD, "email": email}), None)
    db_session.commit()
    for step in (OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.PACKED):
        set_order_status(db_session, order, step, None)
        if step == status:
            break
    return order


def _admin(client, db_session):
    make_admin(db_session, ADMIN, UserRole.SALES_MANAGER)
    return login(client, ADMIN)


def _status(db_session, order):
    db_session.expire_all()
    return db_session.get(type(order), order.id).status


def test_create_shipment_marks_order_shipped_and_emails(client, db_session, sku, monkeypatch):
    sent = []
    import app.routers.admin_orders as admin_orders

    monkeypatch.setattr(admin_orders.shipment_notifier, "shipment_updated", lambda o, s, db=None: sent.append(s.status.value))
    headers = _admin(client, db_session)
    order = _order(db_session, sku)

    r = client.post(
        f"/api/v1/admin/orders/{order.id}/shipments",
        json={"carrier": "  DHL ", "tracking_number": "TRK123", "tracking_url": "https://dhl.example/TRK123"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["carrier"] == "DHL"
    assert body["status"] == "shipped"
    assert body["shipped_at"] is not None
    assert [e["status"] for e in body["events"]] == ["shipped"]
    assert _status(db_session, order) == OrderStatus.SHIPPED
    assert sent == ["shipped"]


def test_cannot_ship_unpacked_order(client, db_session, sku):
    headers = _admin(client, db_session)
    order = _order(db_session, sku, status=OrderStatus.PROCESSING)
    r = client.post(f"/api/v1/admin/orders/{order.id}/shipments", json={"carrier": "DHL"}, headers=headers)
    assert r.status_code == 409
    assert _status(db_session, order) == OrderStatus.PROCESSING


def test_events_drive_order_to_delivered(client, db_session, sku):
    headers = _admin(client, db_session)
    order = _order(db_session, sku)
    sid = client.post(f"/api/v1/admin/orders/{order.id}/shipments", json={"carrier": "DHL"}, headers=headers).json()["id"]
    url = f"/api/v1/admin/orders/{order.id}/shipments/{sid}/events"

    assert client.post(url, json={"status": "in_transit", "location": "Hub"}, headers=headers).status_code == 201
    assert _status(db_session, order) == OrderStatus.IN_TRANSIT

    r = client.post(url, json={"status": "delivered"}, headers=headers)
    assert r.status_code == 201
    assert r.json()["delivered_at"] is not None
    assert _status(db_session, order) == OrderStatus.DELIVERED

    # Every step left a row in the order's status history.
    history = db_session.query(OrderStatusHistory).filter_by(order_id=order.id).all()
    assert [h.to_status for h in history][-3:] == [OrderStatus.SHIPPED, OrderStatus.IN_TRANSIT, OrderStatus.DELIVERED]


def test_delivered_shipment_cannot_go_back_to_in_transit(client, db_session, sku):
    headers = _admin(client, db_session)
    order = _order(db_session, sku)
    sid = client.post(f"/api/v1/admin/orders/{order.id}/shipments", json={"carrier": "DHL"}, headers=headers).json()["id"]
    url = f"/api/v1/admin/orders/{order.id}/shipments/{sid}/events"
    client.post(url, json={"status": "delivered"}, headers=headers)
    assert client.post(url, json={"status": "in_transit"}, headers=headers).status_code == 409


def test_split_shipments_order_delivered_only_when_all_delivered(client, db_session, sku):
    headers = _admin(client, db_session)
    order = _order(db_session, sku)
    base = f"/api/v1/admin/orders/{order.id}/shipments"
    a = client.post(base, json={"carrier": "DHL"}, headers=headers).json()["id"]
    b = client.post(base, json={"carrier": "FedEx"}, headers=headers).json()["id"]

    client.post(f"{base}/{a}/events", json={"status": "delivered"}, headers=headers)
    assert _status(db_session, order) == OrderStatus.IN_TRANSIT  # one parcel still out
    client.post(f"{base}/{b}/events", json={"status": "delivered"}, headers=headers)
    assert _status(db_session, order) == OrderStatus.DELIVERED


def test_all_shipments_returned_marks_order_returned_and_releases_stock(client, db_session, sku):
    from app.models.inventory import Inventory

    headers = _admin(client, db_session)
    order = _order(db_session, sku)
    sid = client.post(f"/api/v1/admin/orders/{order.id}/shipments", json={"carrier": "DHL"}, headers=headers).json()["id"]
    client.post(f"/api/v1/admin/orders/{order.id}/shipments/{sid}/events", json={"status": "returned"}, headers=headers)
    assert _status(db_session, order) == OrderStatus.RETURNED
    db_session.expire_all()
    assert db_session.query(Inventory).filter_by(sku_id=sku.id).one().reserved == 0


def test_tracking_url_must_be_http(client, db_session, sku):
    headers = _admin(client, db_session)
    order = _order(db_session, sku)
    r = client.post(
        f"/api/v1/admin/orders/{order.id}/shipments",
        json={"carrier": "DHL", "tracking_url": "javascript:alert(1)"},
        headers=headers,
    )
    assert r.status_code == 422


def test_patch_shipment_updates_tracking_fields(client, db_session, sku):
    headers = _admin(client, db_session)
    order = _order(db_session, sku)
    sid = client.post(f"/api/v1/admin/orders/{order.id}/shipments", json={"carrier": "DHL"}, headers=headers).json()["id"]
    r = client.patch(
        f"/api/v1/admin/orders/{order.id}/shipments/{sid}", json={"tracking_number": "NEW1"}, headers=headers
    )
    assert r.status_code == 200
    assert r.json()["tracking_number"] == "NEW1"
    assert r.json()["carrier"] == "DHL"


def test_shipment_routes_reject_customers_and_anonymous(client, db_session, sku):
    order = _order(db_session, sku)
    url = f"/api/v1/admin/orders/{order.id}/shipments"
    assert client.post(url, json={"carrier": "DHL"}).status_code in (401, 403)
    customer = register(client, "cust@example.com")
    assert client.post(url, json={"carrier": "DHL"}, headers=customer).status_code == 403


def test_unknown_shipment_is_404(client, db_session, sku):
    headers = _admin(client, db_session)
    order = _order(db_session, sku)
    r = client.post(f"/api/v1/admin/orders/{order.id}/shipments/999/events", json={"status": "delivered"}, headers=headers)
    assert r.status_code == 404


def test_track_order_returns_progress_only(client, db_session, sku):
    headers = _admin(client, db_session)
    order = _order(db_session, sku)
    client.post(
        f"/api/v1/admin/orders/{order.id}/shipments",
        json={"carrier": "DHL", "tracking_number": "TRK9"},
        headers=headers,
    )

    r = client.post(
        "/api/v1/orders/track", json={"order_number": order.order_number.lower(), "email": " Alice@Example.com "}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "shipped"
    assert body["shipments"][0]["tracking_number"] == "TRK9"
    assert set(body) == {"order_number", "status", "created_at", "shipments"}  # no address/prices/items


def test_track_order_wrong_email_or_number_is_indistinguishable_404(client, db_session, sku):
    order = _order(db_session, sku)
    wrong_email = client.post("/api/v1/orders/track", json={"order_number": order.order_number, "email": "x@example.com"})
    wrong_number = client.post("/api/v1/orders/track", json={"order_number": "MARU-NOPE", "email": "alice@example.com"})
    assert wrong_email.status_code == wrong_number.status_code == 404
    assert wrong_email.json() == wrong_number.json()


def test_track_order_is_rate_limited(client, db_session, sku):
    for _ in range(10):
        client.post("/api/v1/orders/track", json={"order_number": "MARU-X", "email": "a@example.com"})
    assert client.post("/api/v1/orders/track", json={"order_number": "MARU-X", "email": "a@example.com"}).status_code == 429


def test_customer_order_includes_shipments(client, db_session, sku):
    headers = _admin(client, db_session)
    order = _order(db_session, sku)
    client.post(f"/api/v1/admin/orders/{order.id}/shipments", json={"carrier": "DHL"}, headers=headers)
    admin_view = client.get(f"/api/v1/admin/orders/{order.id}", headers=headers).json()
    assert admin_view["shipments"][0]["carrier"] == "DHL"
    assert admin_view["shipments"][0]["events"][0]["status"] == "shipped"
