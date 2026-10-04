"""PRD ТЗ№1 §64 acceptance criteria, end to end over HTTP, as a guest customer and a sales manager:

find a product -> pick a variant -> add to cart -> order without registering -> pay -> order exists ->
stock reserved -> manager sees it -> customer is notified -> sent to CRM/ERP hooks -> tracking appears ->
customer sees the status -> admin changes it -> history is kept -> documents and payment ledger agree."""

import base64
import json
import time

import requests

from app.models.enums import OrderStatus, UserRole
from app.models.inventory import Inventory
from app.models.webhook_endpoint import WebhookEndpoint
from conftest import CHECKOUT_PAYLOAD, login, make_admin

API = "/api/v1"


def _payme(client, method, params, rid=1):
    auth = "Basic " + base64.b64encode(b"Paycom:test-payme-key").decode()
    return client.post(f"{API}/payments/payme/webhook", json={"id": rid, "method": method, "params": params}, headers={"Authorization": auth}).json()


def test_guest_purchase_from_search_to_delivery(client, db_session, sku, monkeypatch):
    sent_mail, hooks = [], []
    from app.services.notifications.email import EmailNotifier

    monkeypatch.setattr(EmailNotifier, "_send", lambda self, to, subject, body: sent_mail.append((to, subject)))
    monkeypatch.setattr(requests, "post", lambda url, data=None, headers=None, timeout=None, allow_redirects=None, **k: hooks.append(headers["X-Maru-Event"]) or type("R", (), {"status_code": 200})())
    db_session.add(WebhookEndpoint(url="http://127.0.0.1:9/erp", secret="s3cret", events="*"))
    db_session.commit()

    # 1-2. The customer finds the product and picks a variant
    found = client.get(f"{API}/products/", params={"q": "container"}).json()
    assert [p["slug"] for p in found] == ["food-container"]
    product = client.get(f"{API}/products/{found[0]['slug']}").json()
    variant = product["variants"][0]
    chosen = variant["skus"][0]
    assert chosen["available_quantity"] == 10

    # 3. Adds to the cart (guest: the cart is identified by a token)
    first = client.get(f"{API}/cart/")
    token = first.headers["X-Cart-Token"]
    cart_headers = {"X-Cart-Token": token}
    cart = client.post(f"{API}/cart/items", json={"sku_id": chosen["id"], "quantity": 3}, headers=cart_headers).json()
    assert cart["item_count"] == 3 and float(cart["subtotal"]) == 30.0

    # 4. Orders without registering; 6. the order is created with stock reserved at once
    r = client.post(f"{API}/orders/", json={**CHECKOUT_PAYLOAD, "payment_method": "payme"}, headers=cart_headers)
    assert r.status_code == 201, r.text
    created = r.json()
    order_id, order_token = created["id"], created["guest_order_token"]
    guest = {"X-Order-Token": order_token}
    assert db_session.query(Inventory).one().reserved == 3
    assert (float(created["total_amount"]) - float(created["subtotal_amount"]) - float(created["delivery_amount"]) - float(created["tax_amount"]) + float(created["discount_amount"])) == 0  # Subtotal + Delivery + Tax - Discount = Total

    # 5. Pays (Payme protocol): the order becomes Paid
    amount = int(round(float(created["total_amount"]) * 100))
    assert "result" in _payme(client, "CheckPerformTransaction", {"amount": amount, "account": {"order_id": str(order_id)}})
    assert "result" in _payme(client, "CreateTransaction", {"id": "tx-e2e", "time": int(time.time() * 1000), "amount": amount, "account": {"order_id": str(order_id)}}, 2)
    assert _payme(client, "PerformTransaction", {"id": "tx-e2e"}, 3)["result"]["state"] == 2
    seen = client.get(f"{API}/orders/{order_id}", headers=guest).json()
    assert seen["status"] == "paid" and seen["payment_status"] == "paid"                 # 14. customer sees the status

    # 8. A manager sees the order; payment ledger and generated documents agree
    make_admin(db_session, "sales@example.com", UserRole.SALES_MANAGER)
    manager = login(client, "sales@example.com")
    assert order_id in [o["id"] for o in client.get(f"{API}/admin/orders/", headers=manager).json()]
    payments = client.get(f"{API}/admin/orders/{order_id}/payments", headers=manager).json()
    assert [(p["status"], p["provider_transaction_id"]) for p in payments] == [("paid", "tx-e2e")]
    docs = {d["doc_type"] for d in client.get(f"{API}/orders/{order_id}/documents", headers=guest).json()}
    assert {"invoice"} <= docs

    # 9-10. The customer was e-mailed and the integration hooks fired (CRM/ERP side)
    assert any("received" in s.lower() or "paid" in s.lower() or "order" in s.lower() for _to, s in sent_mail)
    assert {"order.created", "order.paid", "payment.success"} <= set(hooks)

    # 11. After shipping, tracking information appears; 15. the admin moves the status; 16. history is kept
    for status in ("processing", "packed"):
        assert client.patch(f"{API}/admin/orders/{order_id}/status", json={"status": status}, headers=manager).status_code == 200
    ship = client.post(f"{API}/admin/orders/{order_id}/shipments", json={"carrier": "MARU"}, headers=manager)
    assert ship.status_code == 201, ship.text
    tracking = ship.json()["tracking_number"]
    assert tracking
    after = client.get(f"{API}/orders/{order_id}", headers=guest).json()
    assert after["status"] == "shipped" and after["shipments"][0]["tracking_number"] == tracking
    history = [h["to_status"] for h in after["status_history"]]
    assert history == ["new", "payment_pending", "paid", "processing", "packed", "shipped"]
    assert "order.shipped" in hooks

    # the order can also be tracked publicly with number + e-mail (no account needed)
    t = client.post(f"{API}/orders/track", json={"order_number": created["order_number"], "email": CHECKOUT_PAYLOAD["email"]})
    assert t.status_code == 200
    assert json.dumps(t.json()).count(tracking) >= 1
    assert db_session.query(Inventory).one().stock == 10  # stock is only consumed when delivered; reservation stays
