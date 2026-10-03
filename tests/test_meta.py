"""Meta Conversions API forwarding: mapping, privacy, queueing, token never leaks."""

import logging

import pytest
import requests

from app.config import settings
from app.core.request_id import ads_consent_var
from app.models.job import Job
from app.services import jobs
from app.services.analytics import record_event
from app.services.integrations import meta


@pytest.fixture()
def configured(monkeypatch):
    monkeypatch.setattr(settings, "META_PIXEL_ID", "999")
    monkeypatch.setattr(settings, "META_CAPI_TOKEN", "TOPSECRET")
    monkeypatch.setattr(settings, "META_TEST_EVENT_CODE", "")
    token = ads_consent_var.set(True)  # the visitor accepted analytics
    yield
    ads_consent_var.reset(token)


class _Resp:
    status_code = 200
    text = "{}"

    def raise_for_status(self):
        pass


def test_purchase_payload_shape_and_privacy():
    p = meta.build_payload("purchase", 7, "tok", {"order_id": 5, "value": "12.50", "currency": "USD", "email": "a@b.c"}, event_time=1700000000)
    (e,) = p["data"]
    assert e["event_name"] == "Purchase" and e["event_time"] == 1700000000 and e["action_source"] == "website"
    assert e["custom_data"] == {"value": 12.5, "currency": "USD", "order_id": 5}
    assert e["event_id"] == "purchase-5"
    assert list(e["user_data"]) == ["external_id"] and len(e["user_data"]["external_id"][0]) == 64
    assert "a@b.c" not in str(p)


def test_unmapped_and_incomplete_events_are_skipped():
    assert meta.build_payload("login", 1, None, {}) is None
    assert meta.build_payload("admin_login", 1, None, {}) is None
    assert meta.build_payload("purchase", 1, None, {"value": "5"}) is None  # no currency


def test_test_event_code_is_attached(monkeypatch):
    monkeypatch.setattr(settings, "META_TEST_EVENT_CODE", "TEST123")
    assert meta.build_payload("add_to_cart", None, "s", {"value": 1, "currency": "USD"})["test_event_code"] == "TEST123"


def test_nothing_sent_when_unconfigured(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: pytest.fail("must not call Meta"))
    meta.forward("purchase", None, "s", {"value": 1, "currency": "USD"})


def test_record_event_forwards_with_bearer_header(configured, db_session, monkeypatch):
    calls = []
    monkeypatch.setattr(requests, "post", lambda url, headers=None, json=None, timeout=None: calls.append((url, headers, json)) or _Resp())
    record_event(db_session, "add_to_cart", session_id="abc", value="3", currency="USD")
    (url, headers, body), = calls
    assert url.endswith("/999/events") and headers == {"Authorization": "Bearer TOPSECRET"}
    assert "TOPSECRET" not in url and body["data"][0]["event_name"] == "AddToCart"


def test_failures_do_not_break_callers_or_leak_the_token(configured, db_session, monkeypatch, caplog):
    def boom(url, headers=None, json=None, timeout=None):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(requests, "post", boom)
    with caplog.at_level(logging.DEBUG):
        record_event(db_session, "add_to_cart", session_id="abc", value="3", currency="USD")
    assert "TOPSECRET" not in caplog.text


def test_async_mode_queues_and_retries(configured, db_session, monkeypatch):
    monkeypatch.setattr(settings, "JOBS_ASYNC", True)
    monkeypatch.setattr(requests, "post", lambda *a, **k: pytest.fail("must not send inline"))
    record_event(db_session, "add_to_cart", session_id="abc", value="3", currency="USD")
    job = db_session.query(Job).filter_by(job_type="meta.send").one()

    def boom(url, headers=None, json=None, timeout=None):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(requests, "post", boom)
    jobs.run_pending(db_session, "w")
    db_session.refresh(job)
    assert job.status == "pending" and job.attempts == 1 and "TOPSECRET" not in (job.last_error or "") + job.payload
