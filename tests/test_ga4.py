"""GA4 Measurement Protocol forwarding: payload shape, privacy, queueing, no secret leaks."""

import logging

import pytest
import requests

from app.config import settings
from app.models.job import Job
from app.services import jobs
from app.services.analytics import record_event
from app.services.integrations import ga4


@pytest.fixture()
def configured(monkeypatch):
    monkeypatch.setattr(settings, "GA4_MEASUREMENT_ID", "G-TEST")
    monkeypatch.setattr(settings, "GA4_API_SECRET", "TOPSECRET")
    monkeypatch.setattr(settings, "GA4_DEBUG", False)


class _Resp:
    status_code = 204

    def raise_for_status(self):
        pass


def test_payload_is_anonymous_and_ga4_shaped():
    p = ga4.build_payload("purchase", 7, "tok", {"order_id": 5, "value": "12.50", "currency": "USD", "email": None, "nested": {"a": 1}})
    assert p["events"] == [{"name": "purchase", "params": {"transaction_id": 5, "value": 12.5, "currency": "USD"}}]
    assert p["client_id"] not in ("7", "user:7", "tok") and len(p["client_id"]) == 32
    assert p["client_id"] == ga4.build_payload("login", 7, None, {})["client_id"]  # stable per user
    assert ga4.build_payload("admin_login", 1, None, {}) is None
    assert ga4.build_payload("bad name!", 1, None, {}) is None


def test_nothing_is_sent_when_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "GA4_API_SECRET", "")
    monkeypatch.setattr(requests, "post", lambda *a, **k: pytest.fail("must not call Google"))
    ga4.forward("purchase", None, "s", {"value": 1})


def test_record_event_forwards_inline(configured, db_session, monkeypatch):
    calls = []
    monkeypatch.setattr(requests, "post", lambda url, params=None, json=None, timeout=None: calls.append((url, params, json)) or _Resp())
    record_event(db_session, "add_to_cart", session_id="abc", value="3")
    (url, params, body), = calls
    assert url == ga4.COLLECT_URL and params == {"measurement_id": "G-TEST", "api_secret": "TOPSECRET"}
    assert body["events"][0]["name"] == "add_to_cart"


def test_failure_never_breaks_the_caller_or_logs_the_secret(configured, db_session, monkeypatch, caplog):
    def boom(url, params=None, json=None, timeout=None):
        raise requests.ConnectionError(f"{url}?api_secret={params['api_secret']}")

    monkeypatch.setattr(requests, "post", boom)
    with caplog.at_level(logging.DEBUG):
        record_event(db_session, "login", session_id="abc")
    assert "TOPSECRET" not in caplog.text


def test_async_mode_queues_and_the_job_retries_without_leaking(configured, db_session, monkeypatch):
    monkeypatch.setattr(settings, "JOBS_ASYNC", True)
    monkeypatch.setattr(requests, "post", lambda *a, **k: pytest.fail("must not send inline"))
    record_event(db_session, "purchase", session_id="abc", order_id=1, value="9")
    job = db_session.query(Job).one()
    assert job.job_type == "ga4.send"

    def boom(url, params=None, json=None, timeout=None):
        raise requests.ConnectionError(f"{url}?api_secret={params['api_secret']}")

    monkeypatch.setattr(requests, "post", boom)
    jobs.run_pending(db_session, "w")
    db_session.refresh(job)
    assert job.status == "pending" and job.attempts == 1
    assert "TOPSECRET" not in (job.last_error or "") and "TOPSECRET" not in job.payload
