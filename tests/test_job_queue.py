"""PRD ТЗ№3 §88-89 / ТЗ№4 §50-54: background jobs, retries, dead letters, signed webhooks."""

import json
import time
from datetime import timedelta
from types import SimpleNamespace

from app.config import settings
from app.models.enums import UserRole
from app.models.job import JOB_DEAD, JOB_DONE, JOB_PENDING, Job
from app.services import jobs, webhooks
from app.services.notifications import queued
from app.tasks.check_alerts import run_checks
from conftest import login, make_admin


def _boom_handler(calls):
    @jobs.job_handler("test.boom")
    def boom(db, payload):
        calls.append(payload)
        raise RuntimeError("smtp down")


def test_failed_job_retries_with_backoff_then_dies(db_session):
    calls = []
    _boom_handler(calls)
    job = jobs.enqueue(db_session, "test.boom", {"x": 1}, max_attempts=3)
    for attempt in (1, 2, 3):
        job.run_at = jobs._now() - timedelta(seconds=1)  # make it due
        db_session.commit()
        assert jobs.run_pending(db_session, "w1") == 1
        db_session.refresh(job)
        assert job.attempts == attempt
    assert job.status == JOB_DEAD and "smtp down" in job.last_error
    assert len(calls) == 3
    assert jobs.run_pending(db_session, "w1") == 0

    assert jobs.queue_stats(db_session)["dead"] == 1
    assert jobs.retry_dead(db_session, job.id).status == JOB_PENDING


def test_backoff_delays_the_retry(db_session):
    _boom_handler([])
    job = jobs.enqueue(db_session, "test.boom")
    assert jobs.run_pending(db_session, "w1") == 1
    db_session.refresh(job)
    assert job.status == JOB_PENDING and job.run_at > jobs._now() + timedelta(seconds=30)
    assert jobs.run_pending(db_session, "w1") == 0  # not due yet


def test_success_and_dedupe(db_session):
    seen = []

    @jobs.job_handler("test.ok")
    def ok(db, payload):
        seen.append(payload["n"])

    first = jobs.enqueue(db_session, "test.ok", {"n": 1}, dedupe_key="k1")
    assert jobs.enqueue(db_session, "test.ok", {"n": 2}, dedupe_key="k1") is None
    assert jobs.run_pending(db_session, "w1") == 1
    db_session.refresh(first)
    assert first.status == JOB_DONE and seen == [1]


def test_unknown_handler_and_stale_recovery(db_session):
    job = jobs.enqueue(db_session, "nobody.handles.this")
    jobs.run_pending(db_session, "w1")
    db_session.refresh(job)
    assert job.status == JOB_DEAD

    stuck = jobs.enqueue(db_session, "test.ok", {"n": 9})
    stuck.status, stuck.locked_at = "running", jobs._now() - timedelta(hours=1)
    db_session.commit()
    assert jobs.recover_stale(db_session) == 1
    db_session.refresh(stuck)
    assert stuck.status == JOB_PENDING


def test_notifications_are_queued_when_async_and_missing_order_is_permanent(db_session, monkeypatch):
    monkeypatch.setattr(settings, "JOBS_ASYNC", True)
    n = queued.QueuedNotifier()
    order = SimpleNamespace(id=4040)
    n.order_created(order, db=db_session)
    n.order_created(order, db=db_session)  # a retried request must not double-queue
    assert db_session.query(Job).count() == 1

    jobs.run_pending(db_session, "w1")
    job = db_session.query(Job).one()
    assert job.status == JOB_DEAD and job.attempts == 1  # order missing: no pointless retries


def test_notifications_inline_when_not_async(db_session, monkeypatch):
    monkeypatch.setattr(settings, "JOBS_ASYNC", False)
    sent = []
    monkeypatch.setattr(queued.EmailNotifier, "order_created", lambda self, o, db=None: sent.append(o.id))
    queued.QueuedNotifier().order_created(SimpleNamespace(id=1), db=db_session)
    assert sent == [1] and db_session.query(Job).count() == 0


def test_alert_for_dead_jobs(db_session):
    job = jobs.enqueue(db_session, "nobody.handles.this")
    jobs.run_pending(db_session, "w1")
    sent = []
    notifier = SimpleNamespace(admin_alert=lambda s, b: sent.append(s), _send=lambda *a: sent.append(a))
    keys = run_checks(db_session, notifier=notifier)
    assert "jobs_dead" in keys


def test_admin_jobs_api(client, db_session):
    make_admin(db_session, "root@example.com", UserRole.SUPER_ADMIN)
    h = login(client, "root@example.com")
    job = jobs.enqueue(db_session, "nobody.handles.this")
    jobs.run_pending(db_session, "w1")

    r = client.get("/api/v1/admin/jobs/?status_filter=dead", headers=h)
    assert r.status_code == 200 and [j["id"] for j in r.json()] == [job.id]
    assert client.get("/api/v1/admin/jobs/stats", headers=h).json()["dead"] == 1
    assert client.post(f"/api/v1/admin/jobs/{job.id}/retry", headers=h).json()["status"] == "pending"
    assert client.post(f"/api/v1/admin/jobs/{job.id}/retry", headers=h).status_code == 404
    assert client.get("/api/v1/admin/jobs/stats").status_code == 401


def _post(client, provider, body, secret="s3cret", ts=None, event_id="evt-1", sig=None):
    ts = str(int(time.time())) if ts is None else ts
    raw = json.dumps(body).encode()
    headers = {
        "X-Maru-Timestamp": ts,
        "X-Maru-Signature": sig if sig is not None else webhooks.sign(secret, ts, raw),
        "X-Maru-Event-Id": event_id,
        "Content-Type": "application/json",
    }
    return client.post(f"/api/v1/integrations/{provider}/webhook", content=raw, headers=headers)


def test_webhook_signature_idempotency_and_queueing(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "WEBHOOK_SECRETS", json.dumps({"erp": "s3cret"}))

    assert _post(client, "unknown", {}).status_code == 404
    assert _post(client, "erp", {"a": 1}, sig="bad").status_code == 401
    assert _post(client, "erp", {"a": 1}, ts=str(int(time.time()) - 3600)).status_code == 401
    assert db_session.query(Job).count() == 0

    r = _post(client, "erp", {"a": 1})
    assert r.status_code == 202 and r.json()["status"] == "accepted"
    r = _post(client, "erp", {"a": 1})
    assert r.status_code == 202 and r.json()["status"] == "duplicate"
    db_session.expire_all()
    (job,) = db_session.query(Job).all()
    assert job.job_type == "webhook.received" and json.loads(job.payload)["provider"] == "erp"
    assert jobs.run_pending(db_session, "w1") == 1
