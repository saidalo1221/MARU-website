"""Integration health metrics (PRD ТЗ№4 §66) and the alert task (§67)."""

import time
from datetime import datetime, timedelta

from app.config import settings
from app.models.audit_log import AuditLog
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.enums import OrderStatus, UserRole
from app.models.integration_log import IntegrationLog, IntegrationLogStatus as S
from app.models.order_status_history import OrderStatusHistory
from app.schemas.order import CheckoutRequest
from app.services.integrations.health import integration_metrics, unresolved_calls
from app.services.integrations.log import run_with_log
from app.services.order_service import create_order
from app.tasks.check_alerts import run_checks
from conftest import CHECKOUT_PAYLOAD, login, make_admin

NOW = datetime(2026, 10, 1, 12, 0, 0)


class _Recorder:
    def __init__(self):
        self.sent = []

    def admin_alert(self, subject, body):
        self.sent.append(subject)


def _log(db, integration, entity_id, status, minutes_ago, duration_ms=None):
    db.add(
        IntegrationLog(
            integration=integration, operation="push", internal_entity="order", internal_id=entity_id,
            status=status, created_at=NOW - timedelta(minutes=minutes_ago), duration_ms=duration_ms,
        )
    )


def test_run_with_log_records_call_duration(db_session):
    run_with_log(db_session, "t", "op", "x", 1, lambda: time.sleep(0.03) or True)
    row = db_session.query(IntegrationLog).one()
    assert row.duration_ms is not None and row.duration_ms >= 25


def test_unresolved_calls_track_first_failure_and_reset_on_success(db_session):
    _log(db_session, "crm", 1, S.FAILED, 50)
    _log(db_session, "crm", 1, S.FAILED, 30)  # still the same outage, since = 50 min ago
    _log(db_session, "crm", 2, S.FAILED, 40)
    _log(db_session, "crm", 2, S.SUCCESS, 10)  # resolved
    _log(db_session, "crm", 3, S.DEAD_LETTER, 20)
    db_session.commit()

    calls = {(c.status, c.since) for c in unresolved_calls(db_session)}
    assert calls == {(S.FAILED, NOW - timedelta(minutes=50)), (S.DEAD_LETTER, NOW - timedelta(minutes=20))}


def test_metrics_summarise_latency_backlog_and_lag(db_session):
    _log(db_session, "crm", 1, S.SUCCESS, 5, duration_ms=100)
    _log(db_session, "crm", 4, S.SUCCESS, 5, duration_ms=300)
    _log(db_session, "crm", 5, S.FAILED, 50, duration_ms=50)
    _log(db_session, "crm", 3, S.DEAD_LETTER, 20)
    db_session.commit()

    m = integration_metrics(db_session, NOW)["crm"]
    assert m["avg_latency_ms"] == 150 and m["max_latency_ms"] == 300
    assert m["pending_retries"] == 1
    assert m["dead_letters"] == 1
    assert m["sync_lag_seconds"] == 50 * 60  # the oldest unresolved failure


def test_health_endpoint_includes_metrics(client, db_session):
    now = datetime.utcnow()
    db_session.add(
        IntegrationLog(integration="crm_bitrix24", operation="push", internal_entity="order", internal_id=1,
                       status=S.FAILED, created_at=now - timedelta(minutes=30), duration_ms=120)
    )
    db_session.commit()
    make_admin(db_session, "root@example.com", UserRole.SUPER_ADMIN)
    r = client.get("/api/v1/admin/integration-logs/health", headers=login(client, "root@example.com"))
    assert r.status_code == 200, r.text
    crm = {h["integration"]: h for h in r.json()}["crm_bitrix24"]
    assert crm["pending_retries"] == 1 and crm["dead_letters_open"] == 0
    assert crm["avg_latency_ms"] == 120
    assert 29 * 60 <= crm["sync_lag_seconds"] <= 31 * 60


def test_dead_letter_alert_is_sent_once_per_cooldown(db_session):
    _log(db_session, "crm", 1, S.DEAD_LETTER, 5)
    db_session.commit()
    rec = _Recorder()

    assert run_checks(db_session, rec, NOW) == ["dead_letter:crm"]
    assert "exhausted their retries" in rec.sent[0]
    assert run_checks(db_session, rec, NOW + timedelta(minutes=30)) == []  # cooldown
    assert len(rec.sent) == 1
    later = NOW + timedelta(minutes=settings.ALERT_COOLDOWN_MINUTES + 1)
    assert "dead_letter:crm" in run_checks(db_session, rec, later)  # sent again after cooldown
    assert db_session.query(AuditLog).filter_by(action="alert_sent").count() == 3  # dead-letter twice + sync-lag once


def test_sync_lag_and_backlog_alerts(db_session, monkeypatch):
    monkeypatch.setattr(settings, "ALERT_RETRY_BACKLOG", 2)
    monkeypatch.setattr(settings, "ALERT_SYNC_LAG_MINUTES", 45)
    _log(db_session, "crm", 1, S.FAILED, 50)
    _log(db_session, "crm", 2, S.FAILED, 5)
    db_session.commit()

    assert set(run_checks(db_session, _Recorder(), NOW)) == {"sync_lag:crm", "retry_backlog"}


def test_nothing_is_sent_when_all_is_well(db_session):
    _log(db_session, "crm", 1, S.SUCCESS, 5)
    db_session.commit()
    rec = _Recorder()
    assert run_checks(db_session, rec, NOW) == [] and rec.sent == []


def test_payment_failure_spike_alert(db_session, sku, monkeypatch):
    monkeypatch.setattr(settings, "ALERT_PAYMENT_FAILURES", 2)
    cart = Cart(token="alerts-cart")
    db_session.add(cart)
    db_session.flush()
    db_session.add(CartItem(cart_id=cart.id, sku_id=sku.id, quantity=1))
    db_session.commit()
    db_session.refresh(cart)
    order = create_order(db_session, cart, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()
    for minutes_ago in (10, 20):
        db_session.add(
            OrderStatusHistory(order_id=order.id, to_status=OrderStatus.PAYMENT_FAILED, created_at=NOW - timedelta(minutes=minutes_ago))
        )
    db_session.commit()

    assert run_checks(db_session, _Recorder(), NOW) == ["payment_failures"]
    # Failures older than an hour don't count.
    assert run_checks(db_session, _Recorder(), NOW + timedelta(hours=2, minutes=settings.ALERT_COOLDOWN_MINUTES)) == []


def test_without_alert_email_nothing_is_sent_or_remembered(db_session, monkeypatch):
    monkeypatch.setattr(settings, "ALERT_EMAIL", None)
    _log(db_session, "crm", 1, S.DEAD_LETTER, 5)
    db_session.commit()
    assert run_checks(db_session, None, NOW) == []
    assert db_session.query(AuditLog).filter_by(action="alert_sent").count() == 0
