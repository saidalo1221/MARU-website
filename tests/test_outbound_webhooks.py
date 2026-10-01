"""PRD ТЗ№1 §37: signed outbound webhooks for order / payment / inventory events."""

import json

import pytest
import requests

from app.config import settings
from app.models.enums import OrderStatus, UserRole
from app.models.job import JOB_DEAD, Job
from app.models.webhook_endpoint import WebhookEndpoint
from app.schemas.order import CheckoutRequest
from app.services import jobs, outbound_webhooks, webhooks
from app.services.order_service import create_order, set_order_status
from conftest import CHECKOUT_PAYLOAD, login, make_admin
from test_orders_reservation import _cart_with

API = "/api/v1/admin/webhooks"


class _Resp:
    def __init__(self, status=200):
        self.status_code = status


@pytest.fixture()
def received(monkeypatch):
    calls = []
    monkeypatch.setattr(requests, "post", lambda url, data=None, headers=None, timeout=None, allow_redirects=None: calls.append((url, data, headers)) or _Resp(200))
    return calls


def _endpoint(db_session, events="*", url="http://127.0.0.1:9/hook"):
    e = WebhookEndpoint(url=url, secret="s3cret", events=events)
    db_session.add(e)
    db_session.commit()
    return e


def _order(db_session, sku):
    order = create_order(db_session, _cart_with(db_session, sku, 1), CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()
    return order


def test_paid_order_posts_two_signed_events(db_session, sku, received):
    _endpoint(db_session)
    order = _order(db_session, sku)
    set_order_status(db_session, order, OrderStatus.PAID, None)

    assert [h["X-Maru-Event"] for _u, _d, h in received] == ["order.paid", "payment.success"]
    url, data, headers = received[0]
    assert webhooks.verify("s3cret", headers["X-Maru-Timestamp"], headers["X-Maru-Signature"], data)  # same scheme as inbound
    body = json.loads(data)
    assert body["event"] == "order.paid" and body["id"] == headers["X-Maru-Event-Id"]
    assert body["data"]["order_number"] == order.order_number and body["data"]["payment_status"] == "paid" and body["data"]["status"] == "paid"
    assert body["data"]["items"][0]["sku"] == "SKU-1000-001" and body["data"]["customer"]["email"] == "alice@example.com"


def test_event_filter_and_inactive_endpoints(db_session, sku, received):
    _endpoint(db_session, events="order.shipped")
    off = _endpoint(db_session)
    off.is_active = False
    db_session.commit()
    order = _order(db_session, sku)
    set_order_status(db_session, order, OrderStatus.PAID, None)
    assert received == []  # nobody listens for order.paid
    set_order_status(db_session, order, OrderStatus.PROCESSING, None)
    set_order_status(db_session, order, OrderStatus.PACKED, None)
    set_order_status(db_session, order, OrderStatus.SHIPPED, None)
    assert [h["X-Maru-Event"] for _u, _d, h in received] == ["order.shipped"]


def test_checkout_emits_order_created(client, db_session, sku, received):
    _endpoint(db_session, events="order.created")
    cart = client.get("/api/v1/cart/")
    tok = cart.headers.get("x-cart-token") or cart.json().get("token")
    client.post("/api/v1/cart/items", json={"sku_id": sku.id, "quantity": 1}, headers={"X-Cart-Token": tok})
    r = client.post("/api/v1/orders/", json={**CHECKOUT_PAYLOAD, "payment_method": "stripe"} if False else CHECKOUT_PAYLOAD, headers={"X-Cart-Token": tok})
    assert r.status_code in (200, 201), r.text
    assert [h["X-Maru-Event"] for _u, _d, h in received] == ["order.created"]


def test_server_errors_retry_and_client_errors_do_not(db_session, sku, monkeypatch):
    monkeypatch.setattr(settings, "JOBS_ASYNC", True)
    _endpoint(db_session)
    order = _order(db_session, sku)

    monkeypatch.setattr(requests, "post", lambda *a, **k: _Resp(503))
    set_order_status(db_session, order, OrderStatus.CANCELLED, None)  # queued only
    job = db_session.query(Job).filter_by(job_type="webhook.deliver").one()
    assert job.status == "pending"
    jobs.run_pending(db_session, "w")
    db_session.refresh(job)
    assert job.status == "pending" and job.attempts == 1 and "HTTP 503" in job.last_error  # will retry later
    ep = db_session.query(WebhookEndpoint).one()
    assert ep.last_status_code == 503

    monkeypatch.setattr(requests, "post", lambda *a, **k: _Resp(410))
    job.run_at = jobs._now()
    db_session.commit()
    jobs.run_pending(db_session, "w")
    db_session.refresh(job)
    assert job.status == JOB_DEAD  # a 4xx will not get better


def test_network_error_is_retried_and_unsafe_urls_refused(db_session, sku, monkeypatch):
    _endpoint(db_session)

    def down(*a, **k):
        raise requests.ConnectionError("no route")

    monkeypatch.setattr(requests, "post", down)
    monkeypatch.setattr(settings, "JOBS_ASYNC", True)
    outbound_webhooks.emit(db_session, "inventory.updated", {"x": 1})
    jobs.run_pending(db_session, "w")
    job = db_session.query(Job).one()
    assert job.status == "pending" and "Network error" in job.last_error

    monkeypatch.setattr(settings, "WEBHOOK_ALLOW_PRIVATE_URLS", False)
    with pytest.raises(outbound_webhooks.UnsafeURLError):
        outbound_webhooks.check_url("http://example.com/hook")           # not https
    with pytest.raises(outbound_webhooks.UnsafeURLError):
        outbound_webhooks.check_url("https://127.0.0.1/hook")            # loopback
    with pytest.raises(outbound_webhooks.UnsafeURLError):
        outbound_webhooks.check_url("https://169.254.169.254/latest")    # cloud metadata


def test_admin_api_secret_shown_once_events_validated_and_ping(client, db_session, received):
    make_admin(db_session, "root@example.com", UserRole.SUPER_ADMIN)
    h = login(client, "root@example.com")
    r = client.post(API + "/", json={"url": "http://127.0.0.1:9/hook", "events": ["order.paid", "payment.success"]}, headers=h)
    assert r.status_code == 201, r.text
    created = r.json()
    assert len(created["secret"]) >= 32
    listing = client.get(API + "/", headers=h).json()
    assert "secret" not in listing[0] and listing[0]["secret_hint"] == "…" + created["secret"][-4:]
    assert client.post(API + "/", json={"url": "http://127.0.0.1:9/hook", "events": ["order.exploded"]}, headers=h).status_code == 422

    r = client.post(f"{API}/{created['id']}/test", headers=h)
    assert r.status_code == 202 and received[-1][2]["X-Maru-Event"] == "ping"
    assert webhooks.verify(created["secret"], received[-1][2]["X-Maru-Timestamp"], received[-1][2]["X-Maru-Signature"], received[-1][1])

    rotated = client.post(f"{API}/{created['id']}/rotate-secret", headers=h).json()["secret"]
    assert rotated != created["secret"]
    assert client.patch(f"{API}/{created['id']}", json={"is_active": False}, headers=h).json()["is_active"] is False
    assert client.delete(f"{API}/{created['id']}", headers=h).status_code == 204
    assert client.get(API + "/", headers={}).status_code == 401


def test_admin_api_refuses_internal_urls_when_not_in_dev_mode(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "WEBHOOK_ALLOW_PRIVATE_URLS", False)
    make_admin(db_session, "root@example.com", UserRole.SUPER_ADMIN)
    h = login(client, "root@example.com")
    r = client.post(API + "/", json={"url": "https://10.0.0.5/hook"}, headers=h)
    assert r.status_code == 400 and "internal" in r.json()["detail"].lower()


def test_inventory_update_emits_event(client, db_session, sku, received):
    _endpoint(db_session, events="inventory.updated")
    make_admin(db_session, "wh@example.com", UserRole.WAREHOUSE_MANAGER)
    h = login(client, "wh@example.com")
    from app.models.inventory import Inventory
    inv = db_session.query(Inventory).one()
    r = client.patch(f"/api/v1/admin/inventory/{inv.sku_id}/{inv.warehouse_id}", json={"stock": 42}, headers=h)
    assert r.status_code == 200, r.text
    body = json.loads(received[-1][1])
    assert body["event"] == "inventory.updated" and body["data"]["stock"] == 42 and body["data"]["sku_code"] == "SKU-1000-001"
