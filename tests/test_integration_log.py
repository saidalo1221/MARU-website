"""Integration retry/DLQ (PRD ТЗ№4 §52-57)."""

from app.models.enums import UserRole
from app.models.integration_log import IntegrationLog, IntegrationLogStatus
from app.services.integrations.log import run_with_log
from app.services.integrations.retry import UnknownIntegrationError, retry_failed_integrations, retry_one
from conftest import login, make_admin


def test_successful_call_logs_success(db_session):
    assert run_with_log(db_session, "test", "op", "widget", 1, lambda: True) is True
    row = db_session.query(IntegrationLog).order_by(IntegrationLog.id.desc()).first()
    assert row.status == IntegrationLogStatus.SUCCESS
    assert row.attempt == 1


def test_repeated_failures_increment_attempt_then_dead_letter(db_session):
    for _ in range(4):
        run_with_log(db_session, "test", "op", "widget", 2, lambda: False, max_attempts=3)
    row = db_session.query(IntegrationLog).filter_by(internal_id=2).order_by(IntegrationLog.id.desc()).first()
    assert row.status == IntegrationLogStatus.DEAD_LETTER
    assert row.attempt >= 3


def test_exception_is_caught_and_logged_not_raised(db_session):
    def boom():
        raise RuntimeError("connector exploded")

    assert run_with_log(db_session, "test", "op", "widget", 3, boom) is False
    row = db_session.query(IntegrationLog).filter_by(internal_id=3).first()
    assert "connector exploded" in row.error_message


def test_retry_failed_integrations_only_retries_latest_failed(db_session, monkeypatch):
    import app.services.integrations.retry as retry_module

    monkeypatch.setitem(retry_module._DISPATCH, ("crm_bitrix24", "push_order"), lambda db, internal_id: True)

    db_session.add(
        IntegrationLog(
            integration="crm_bitrix24", operation="push_order", internal_entity="order", internal_id=99,
            status=IntegrationLogStatus.FAILED, attempt=1,
        )
    )
    db_session.commit()

    retried = retry_failed_integrations(db_session)
    assert retried == 1
    row = db_session.query(IntegrationLog).filter_by(internal_id=99).order_by(IntegrationLog.id.desc()).first()
    assert row.status == IntegrationLogStatus.SUCCESS


def test_retry_one_unknown_integration_raises(db_session):
    try:
        retry_one(db_session, "nonexistent", "op", "thing", 1)
        assert False, "expected UnknownIntegrationError"
    except UnknownIntegrationError:
        pass


def test_admin_manual_retry_endpoint(client, db_session, monkeypatch):
    import app.services.integrations.retry as retry_module

    monkeypatch.setitem(retry_module._DISPATCH, ("crm_bitrix24", "push_order"), lambda db, internal_id: True)

    db_session.add(
        IntegrationLog(
            integration="crm_bitrix24", operation="push_order", internal_entity="order", internal_id=1,
            status=IntegrationLogStatus.DEAD_LETTER, attempt=5,
        )
    )
    db_session.commit()
    log_id = db_session.query(IntegrationLog).first().id

    make_admin(db_session, "super@example.com", UserRole.SUPER_ADMIN)
    headers = login(client, "super@example.com")

    r = client.post(f"/api/v1/admin/integration-logs/{log_id}/retry", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "success"
