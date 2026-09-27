"""Payme/Click webhook protocols and the refund flow (PRD ТЗ№3 §13,
ТЗ№4's payment sections). Written from each provider's documented protocol,
not verified against a live sandbox — see app/routers/payment_webhooks.py's
module docstring."""

import base64
import hashlib
import time

from app.models.enums import OrderStatus, UserRole
from app.models.order import Order
from conftest import CHECKOUT_PAYLOAD, login, make_admin, register


def _payme_auth() -> str:
    return "Basic " + base64.b64encode(b"Paycom:test-payme-key").decode()


def _checkout(client, sku, quantity=2, payment_method="payme"):
    headers = register(client, f"buyer{id(object())}@example.com")
    r = client.post("/api/v1/cart/items", headers=headers, json={"sku_id": sku.id, "quantity": quantity})
    assert r.status_code == 201, r.text
    payload = {**CHECKOUT_PAYLOAD, "payment_method": payment_method}
    r = client.post("/api/v1/orders/", headers=headers, json=payload)
    assert r.status_code == 201, r.text
    return r.json(), headers


def test_payme_full_payment_cycle(client, sku, db_session):
    order, _ = _checkout(client, sku, quantity=2)
    order_id = order["id"]
    amount = int(round(float(order["total_amount"]) * 100))
    auth = _payme_auth()

    rpc = {"id": 1, "method": "CheckPerformTransaction", "params": {"amount": amount, "account": {"order_id": str(order_id)}}}
    r = client.post("/api/v1/payments/payme/webhook", json=rpc, headers={"Authorization": auth})
    assert "result" in r.json(), r.json()

    rpc = {
        "id": 2, "method": "CreateTransaction",
        "params": {"id": "tx-1", "time": int(time.time() * 1000), "amount": amount, "account": {"order_id": str(order_id)}},
    }
    r = client.post("/api/v1/payments/payme/webhook", json=rpc, headers={"Authorization": auth})
    assert "result" in r.json(), r.json()

    order_row = db_session.get(Order, order_id)
    assert order_row.status == OrderStatus.PAYMENT_PENDING

    rpc = {"id": 3, "method": "PerformTransaction", "params": {"id": "tx-1"}}
    r = client.post("/api/v1/payments/payme/webhook", json=rpc, headers={"Authorization": auth})
    assert r.json()["result"]["state"] == 2, r.json()

    db_session.refresh(order_row)
    assert order_row.status == OrderStatus.PAID


def test_payme_wrong_auth_rejected(client, sku):
    order, _ = _checkout(client, sku)
    rpc = {"id": 1, "method": "CheckPerformTransaction", "params": {"amount": 1, "account": {"order_id": str(order["id"])}}}
    r = client.post("/api/v1/payments/payme/webhook", json=rpc, headers={"Authorization": "Basic bad"})
    assert "error" in r.json()


def test_payme_cancel_before_completion_sets_payment_failed_and_releases_stock(client, sku, db_session):
    order, _ = _checkout(client, sku, quantity=4)
    order_id = order["id"]
    amount = int(round(float(order["total_amount"]) * 100))
    auth = _payme_auth()

    rpc = {
        "id": 1, "method": "CreateTransaction",
        "params": {"id": "tx-cancel", "time": int(time.time() * 1000), "amount": amount, "account": {"order_id": str(order_id)}},
    }
    client.post("/api/v1/payments/payme/webhook", json=rpc, headers={"Authorization": auth})

    rpc = {"id": 2, "method": "CancelTransaction", "params": {"id": "tx-cancel", "reason": 3}}
    r = client.post("/api/v1/payments/payme/webhook", json=rpc, headers={"Authorization": auth})
    assert "result" in r.json(), r.json()

    order_row = db_session.get(Order, order_id)
    assert order_row.status == OrderStatus.PAYMENT_FAILED

    from app.models.inventory import Inventory
    inv = db_session.query(Inventory).filter_by(sku_id=sku.id).one()
    assert inv.reserved == 0

    # Retry on the same order re-reserves and can complete.
    rpc = {
        "id": 3, "method": "CreateTransaction",
        "params": {"id": "tx-retry", "time": int(time.time() * 1000), "amount": amount, "account": {"order_id": str(order_id)}},
    }
    r = client.post("/api/v1/payments/payme/webhook", json=rpc, headers={"Authorization": auth})
    assert "result" in r.json(), r.json()
    db_session.refresh(inv)
    assert inv.reserved == 4


def _click_sign(data: dict) -> str:
    action = str(data["action"])
    parts = [str(data.get("click_trans_id", "")), str(data.get("service_id", "")), "test-click-secret",
              str(data.get("merchant_trans_id", ""))]
    if action == "1":
        parts.append(str(data.get("merchant_prepare_id", "")))
    parts += [str(data.get("amount", "")), action, str(data.get("sign_time", ""))]
    return hashlib.md5("".join(parts).encode()).hexdigest()


def test_click_full_payment_cycle(client, sku, db_session):
    order, _ = _checkout(client, sku, quantity=1, payment_method="click")
    order_id = order["id"]
    amount = order["total_amount"]

    prepare = {
        "click_trans_id": "500", "service_id": "test-service", "merchant_trans_id": str(order_id),
        "amount": amount, "action": "0", "sign_time": "2026-01-01 00:00:00",
    }
    prepare["sign_string"] = _click_sign(prepare)
    r = client.post("/api/v1/payments/click/webhook", data=prepare)
    body = r.json()
    assert body["error"] == 0, body

    complete = {
        "click_trans_id": "500", "service_id": "test-service", "merchant_trans_id": str(order_id),
        "merchant_prepare_id": str(body["merchant_prepare_id"]), "amount": amount, "action": "1",
        "sign_time": "2026-01-01 00:00:01", "error": "0",
    }
    complete["sign_string"] = _click_sign(complete)
    r = client.post("/api/v1/payments/click/webhook", data=complete)
    assert r.json()["error"] == 0, r.json()

    order_row = db_session.get(Order, order_id)
    assert order_row.status == OrderStatus.PAID


def test_click_bad_signature_rejected(client, sku):
    order, _ = _checkout(client, sku, payment_method="click")
    data = {"click_trans_id": "1", "service_id": "test-service", "merchant_trans_id": str(order["id"]),
             "amount": order["total_amount"], "action": "0", "sign_time": "x", "sign_string": "wrong"}
    r = client.post("/api/v1/payments/click/webhook", data=data)
    assert r.json()["error"] != 0


def test_refund_blocked_for_payme_but_works_for_a_supported_gateway(client, sku, db_session, monkeypatch):
    order, buyer_headers = _checkout(client, sku, quantity=2)
    order_id = order["id"]
    amount = int(round(float(order["total_amount"]) * 100))
    auth = _payme_auth()

    rpc = {
        "id": 1, "method": "CreateTransaction",
        "params": {"id": "tx-refund", "time": int(time.time() * 1000), "amount": amount, "account": {"order_id": str(order_id)}},
    }
    client.post("/api/v1/payments/payme/webhook", json=rpc, headers={"Authorization": auth})
    rpc = {"id": 2, "method": "PerformTransaction", "params": {"id": "tx-refund"}}
    r = client.post("/api/v1/payments/payme/webhook", json=rpc, headers={"Authorization": auth})
    assert r.json()["result"]["state"] == 2

    admin = make_admin(db_session, "accountant@example.com", UserRole.ACCOUNTANT)
    admin_headers = login(client, "accountant@example.com")

    r = client.post(
        f"/api/v1/admin/orders/{order_id}/refund", headers=admin_headers,
        json={"amount": order["total_amount"], "reason": "test"},
    )
    assert r.status_code == 400
    assert "manually" in r.json()["detail"].lower()

    order_row = db_session.get(Order, order_id)
    assert order_row.status == OrderStatus.PAID  # unchanged by the blocked refund

    # Switch to a gateway with a real refund() and confirm the full path.
    import app.services.refund_service as refund_service

    class _AlwaysSucceedsGateway:
        def refund(self, order, amount):
            return "fake-refund-id"

    monkeypatch.setattr(refund_service, "get_payment_gateway", lambda method: _AlwaysSucceedsGateway())

    r = client.post(
        f"/api/v1/admin/orders/{order_id}/refund", headers=admin_headers,
        json={"amount": order["total_amount"], "reason": "test"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "completed"

    db_session.refresh(order_row)
    assert order_row.status == OrderStatus.REFUNDED


def test_partial_refund_then_full_refund(client, sku, db_session, monkeypatch):
    order, _ = _checkout(client, sku, quantity=3)
    order_id = order["id"]

    from app.services.order_service import set_order_status

    order_row = db_session.get(Order, order_id)
    set_order_status(db_session, order_row, OrderStatus.PAID, None, note="test")

    import app.services.refund_service as refund_service

    class _AlwaysSucceedsGateway:
        def refund(self, order, amount):
            return "fake-refund-id"

    monkeypatch.setattr(refund_service, "get_payment_gateway", lambda method: _AlwaysSucceedsGateway())

    admin = make_admin(db_session, "accountant2@example.com", UserRole.ACCOUNTANT)
    admin_headers = login(client, "accountant2@example.com")

    total = float(order["total_amount"])
    half = round(total / 2, 2)

    r = client.post(f"/api/v1/admin/orders/{order_id}/refund", headers=admin_headers, json={"amount": half})
    assert r.status_code == 201, r.text
    db_session.refresh(order_row)
    assert order_row.status == OrderStatus.PARTIALLY_REFUNDED

    r = client.post(f"/api/v1/admin/orders/{order_id}/refund", headers=admin_headers, json={"amount": total - half})
    assert r.status_code == 201, r.text
    db_session.refresh(order_row)
    assert order_row.status == OrderStatus.REFUNDED

    # A further refund attempt is rejected — nothing left to refund.
    r = client.post(f"/api/v1/admin/orders/{order_id}/refund", headers=admin_headers, json={"amount": "1"})
    assert r.status_code == 400
