"""WhatsApp template messages: only for opted-in customers, right language, token never leaks."""

import logging
from types import SimpleNamespace

import pytest
import requests

from app.config import settings
from app.models.job import JOB_DEAD, Job
from app.schemas.order import CheckoutRequest
from app.services import jobs
from app.services.integrations import whatsapp
from app.services.notifications.queued import QueuedNotifier
from app.services.order_service import create_order
from conftest import CHECKOUT_PAYLOAD
from test_orders_reservation import _cart_with


@pytest.fixture()
def configured(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_TOKEN", "TOPSECRET")
    monkeypatch.setattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "555")


class _Resp:
    status_code = 200
    text = "{}"

    def raise_for_status(self):
        pass


def _order(**kw):
    base = dict(id=1, first_name="Ali", order_number="MR-1", total_amount="10.00", currency="USD", phone="+998 90 123 45 67",
                whatsapp_opt_in=True, language="uz")
    return SimpleNamespace(**{**base, **kw})


def test_number_and_message_shape():
    assert whatsapp.to_wa_number("+998 (90) 123-45-67") == "998901234567"
    assert whatsapp.to_wa_number("90 123 45 67") is None  # no country code: cannot be routed
    m = whatsapp.build_message("998901234567", whatsapp.ORDER_CREATED, "uz", ["Ali", "MR-1", "10 USD"])
    assert m["template"]["name"] == "maru_order_created" and m["template"]["language"] == {"code": "uz"}
    assert [p["text"] for p in m["template"]["components"][0]["parameters"]] == ["Ali", "MR-1", "10 USD"]
    assert whatsapp.build_message("1", "t", "de", ["x"])["template"]["language"]["code"] == "en"
    assert whatsapp.status_text("shipped", "ru") == "Отправлен" and whatsapp.status_text("shipped", "en") == "Shipped"


def test_only_opted_in_customers_are_messaged(configured, monkeypatch):
    sent = []
    monkeypatch.setattr(requests, "post", lambda url, headers=None, json=None, timeout=None: sent.append((url, headers, json)) or _Resp())
    whatsapp.notify_order(None, _order(whatsapp_opt_in=False), whatsapp.ORDER_CREATED, ["a"], "k1")
    assert sent == []
    whatsapp.notify_order(None, _order(), whatsapp.ORDER_CREATED, ["a"], "k2")
    (url, headers, body), = sent
    assert url.endswith("/555/messages") and headers == {"Authorization": "Bearer TOPSECRET"} and body["to"] == "998901234567"


def test_nothing_sent_when_unconfigured(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: pytest.fail("must not call Meta"))
    whatsapp.notify_order(None, _order(), whatsapp.ORDER_CREATED, ["a"], "k")


def test_notifier_sends_whatsapp_for_created_status_and_shipment(configured, db_session, sku, monkeypatch):
    sent = []
    monkeypatch.setattr(requests, "post", lambda url, headers=None, json=None, timeout=None: sent.append(json["template"]["name"]) or _Resp())
    payload = {**CHECKOUT_PAYLOAD, "whatsapp_opt_in": True, "language": "ru"}
    order = create_order(db_session, _cart_with(db_session, sku, 1), CheckoutRequest(**payload), None)
    db_session.commit()
    assert order.whatsapp_opt_in is True and order.language == "ru"

    n = QueuedNotifier()
    monkeypatch.setattr(n._inline, "_send", lambda *a, **k: None)  # e-mail not under test
    n.order_created(order, db=db_session)
    n.order_status_changed(order, "new", "paid", db=db_session)
    n.shipment_updated(order, SimpleNamespace(id=9, status=SimpleNamespace(value="shipped"), tracking_number="T1", carrier="MARU", tracking_url=None), db=db_session)
    assert sent == ["maru_order_created", "maru_order_status", "maru_shipment_update"]


def test_async_queue_retry_and_permanent_refusal(configured, db_session, monkeypatch):
    monkeypatch.setattr(settings, "JOBS_ASYNC", True)
    monkeypatch.setattr(requests, "post", lambda *a, **k: pytest.fail("must not send inline"))
    whatsapp.notify_order(db_session, _order(), whatsapp.ORDER_CREATED, ["a"], "same")
    whatsapp.notify_order(db_session, _order(), whatsapp.ORDER_CREATED, ["a"], "same")  # duplicate request
    job = db_session.query(Job).one()

    def net_down(url, headers=None, json=None, timeout=None):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(requests, "post", net_down)
    jobs.run_pending(db_session, "w")
    db_session.refresh(job)
    assert job.status == "pending" and "TOPSECRET" not in (job.last_error or "") + job.payload

    class Refused(_Resp):
        status_code = 400
        text = "template not approved"

        def raise_for_status(self):
            raise requests.HTTPError(response=self)

    monkeypatch.setattr(requests, "post", lambda *a, **k: Refused())
    job.run_at = jobs._now()
    db_session.commit()
    jobs.run_pending(db_session, "w")
    db_session.refresh(job)
    assert job.status == JOB_DEAD  # a 4xx from Meta will not get better by retrying


def test_failure_in_request_path_is_swallowed_and_logged_without_the_token(configured, monkeypatch, caplog):
    def boom(url, headers=None, json=None, timeout=None):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(requests, "post", boom)
    with caplog.at_level(logging.DEBUG):
        whatsapp.notify_order(None, _order(), whatsapp.ORDER_CREATED, ["a"], "k")
    assert "TOPSECRET" not in caplog.text


def test_site_settings_reports_whether_whatsapp_is_on(client, configured):
    assert client.get("/api/v1/site-settings").json()["whatsapp_enabled"] is True
