"""PRD ТЗ№1 §38-39: web push notifications for order updates and abandoned carts."""

import base64
import json
from datetime import timedelta

import pytest
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from py_vapid import Vapid
from pywebpush import WebPushException

from app.config import settings
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.enums import OrderStatus
from app.models.job import JOB_DEAD, Job
from app.models.push_subscription import PushSubscription
from app.models.user import User
from app.schemas.order import CheckoutRequest
from app.services import jobs, push
from app.services.notifications.queued import QueuedNotifier
from app.services.order_service import create_order
from app.tasks.abandoned_carts import _now, send_abandoned_cart_emails
from conftest import CHECKOUT_PAYLOAD, login, register
from test_orders_reservation import _cart_with


def _b64(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _vapid_pair():
    v = Vapid()
    v.generate_keys()
    pub = v.public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return _b64(pub), _b64(v.private_key.private_numbers().private_value.to_bytes(32, "big"))


def _browser_keys():
    """What a real browser's PushSubscription contains: a P-256 public key and a random auth secret."""
    key = ec.generate_private_key(ec.SECP256R1())
    pub = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return {"p256dh": _b64(pub), "auth": _b64(b"0123456789abcdef")}


@pytest.fixture()
def configured(monkeypatch):
    pub, priv = _vapid_pair()
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", pub)
    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", priv)
    monkeypatch.setattr(settings, "VAPID_SUBJECT", "mailto:shop@example.com")
    return pub


def _user_with_device(client, db_session, endpoint="https://push.example.com/send/abc"):
    register(client, "alice@example.com")
    user = db_session.query(User).filter_by(email="alice@example.com").one()
    db_session.add(PushSubscription(user_id=user.id, endpoint=endpoint, **_browser_keys()))
    db_session.commit()
    return user


def test_a_real_encrypted_message_is_built_with_the_configured_keys(client, db_session, configured, monkeypatch):
    """Runs pywebpush for real (encryption + VAPID signature); only the network call is replaced."""
    user = _user_with_device(client, db_session)
    posted = []

    class Resp:
        status_code = 201
        text = ""
        headers = {}

    monkeypatch.setattr(requests, "post", lambda url, data=None, headers=None, timeout=None, **k: posted.append((url, headers, data)) or Resp())
    assert push.notify_user(db_session, user.id, "MARU-1", "Paid", "/orders/1") == 1
    url, headers, body = posted[0]
    assert url == "https://push.example.com/send/abc"
    assert headers["Authorization"].lower().startswith("vapid ") and headers["Content-Encoding"] == "aes128gcm"
    assert isinstance(body, (bytes, bytearray)) and b"MARU-1" not in bytes(body)   # encrypted, not plain text


def test_subscribe_status_unsubscribe_api(client, db_session, configured):
    assert client.get("/api/v1/push/public-key").json() == {"enabled": True, "public_key": configured}
    register(client, "alice@example.com")
    h = login(client, "alice@example.com")
    sub = {"endpoint": "https://push.example.com/send/xyz", "keys": _browser_keys()}
    assert client.post("/api/v1/push/subscribe", json=sub, headers=h).status_code == 201
    assert client.post("/api/v1/push/subscribe", json=sub, headers=h).json() == {"devices": 1}   # same browser again: no duplicate
    assert client.get("/api/v1/push/status", headers=h).json() == {"enabled": True, "devices": 1}
    assert client.post("/api/v1/push/subscribe", json={**sub, "endpoint": "http://insecure.example.com/x"}, headers=h).status_code == 400
    assert client.post("/api/v1/push/subscribe", json=sub).status_code == 401
    assert client.post("/api/v1/push/unsubscribe", json={"endpoint": sub["endpoint"]}, headers=h).json() == {"devices": 0}


def test_not_configured_means_not_offered_and_nothing_sent(client, db_session):
    assert client.get("/api/v1/push/public-key").json() == {"enabled": False, "public_key": None}
    register(client, "alice@example.com")
    h = login(client, "alice@example.com")
    r = client.post("/api/v1/push/subscribe", json={"endpoint": "https://p.example.com/a", "keys": _browser_keys()}, headers=h)
    assert r.status_code == 503
    assert push.notify_user(db_session, 1, "x", "y") == 0


def test_dead_subscriptions_are_removed_and_failures_do_not_escape(client, db_session, configured, monkeypatch):
    user = _user_with_device(client, db_session)

    class Gone:
        status_code = 410

    def gone(*a, **k):
        raise WebPushException("gone", response=Gone())

    monkeypatch.setattr(push, "_send_one", gone)
    assert push.notify_user(db_session, user.id, "t", "b") == 0
    assert db_session.query(PushSubscription).count() == 0       # the 410 removed it

    def boom(*a, **k):
        raise RuntimeError("network")

    db_session.add(PushSubscription(user_id=user.id, endpoint="https://push.example.com/send/2", **_browser_keys()))
    db_session.commit()
    monkeypatch.setattr(push, "_send_one", boom)
    assert push.notify_user(db_session, user.id, "t", "b") == 0   # swallowed
    assert db_session.query(PushSubscription).count() == 1


def test_async_mode_queues_and_retries_then_drops_dead_devices(client, db_session, configured, monkeypatch):
    monkeypatch.setattr(settings, "JOBS_ASYNC", True)
    user = _user_with_device(client, db_session)
    sent = []
    monkeypatch.setattr(push, "_send_one", lambda sub, msg: sent.append(msg))
    assert push.notify_user(db_session, user.id, "Title", "Body", "/x") == 1 and sent == []
    jobs.run_pending(db_session, "w")
    assert sent == [{"title": "Title", "body": "Body", "url": "/x"}]

    class Gone:
        status_code = 404

    monkeypatch.setattr(push, "_send_one", lambda *a: (_ for _ in ()).throw(WebPushException("gone", response=Gone())))
    push.notify_user(db_session, user.id, "Title", "Body")
    jobs.run_pending(db_session, "w")
    assert db_session.query(Job).filter_by(job_type="push.send", status=JOB_DEAD).count() == 1
    assert db_session.query(PushSubscription).count() == 0


def test_order_updates_push_to_the_owner_only(client, db_session, sku, configured, monkeypatch):
    user = _user_with_device(client, db_session)
    got = []
    monkeypatch.setattr(push, "_send_one", lambda sub, msg: got.append(msg))
    monkeypatch.setattr(QueuedNotifier, "__init__", lambda self: setattr(self, "_inline", type("N", (), {"order_created": lambda *a, **k: None, "order_status_changed": lambda *a, **k: None, "shipment_updated": lambda *a, **k: None})()))
    order = create_order(db_session, _cart_with(db_session, sku, 1), CheckoutRequest(**{**CHECKOUT_PAYLOAD, "language": "en"}), user)
    db_session.commit()
    QueuedNotifier().order_status_changed(order, "new", OrderStatus.PAID.value.lower(), db=db_session)
    assert got and got[0]["title"] == order.order_number and got[0]["body"] == "Paid" and got[0]["url"] == f"/orders/{order.id}"

    guest = create_order(db_session, _cart_with(db_session, sku, 1), CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()
    before = len(got)
    QueuedNotifier().order_status_changed(guest, "new", "paid", db=db_session)
    assert len(got) == before                                      # guests have no devices


def test_abandoned_cart_also_pushes(client, db_session, sku, configured, monkeypatch):
    user = _user_with_device(client, db_session)
    cart = Cart(user_id=user.id)
    db_session.add(cart)
    db_session.flush()
    item = CartItem(cart_id=cart.id, sku_id=sku.id, quantity=1)
    db_session.add(item)
    db_session.commit()
    stamp = _now() - timedelta(hours=30)
    cart.updated_at = item.updated_at = stamp
    db_session.commit()
    got = []
    monkeypatch.setattr(push, "_send_one", lambda sub, msg: got.append(msg))

    class Mail:
        def abandoned_cart(self, *a, **k):
            pass

    assert send_abandoned_cart_emails(db_session, Mail()) == 1
    assert got and got[0]["url"] == "/cart"
