"""'Notify me when back in stock' (PRD ТЗ№2 §20)."""

import pytest

from app.models.inventory import Inventory
from app.models.stock_alert import StockAlert
from app.tasks.notify_back_in_stock import notify_back_in_stock
from conftest import register


class _Recorder:
    def __init__(self):
        self.sent = []

    def back_in_stock(self, email, name, slug, db=None):
        self.sent.append((email, name, slug))


@pytest.fixture()
def out_of_stock(db_session, sku):
    inv = db_session.query(Inventory).filter_by(sku_id=sku.id).one()
    inv.stock = 0
    db_session.commit()
    return sku



def test_guest_can_subscribe_for_out_of_stock_sku(client, out_of_stock, db_session):
    r = client.post("/api/v1/stock-alerts/", json={"sku_id": out_of_stock.id, "email": "Wait@Example.com"})
    assert r.status_code == 201, r.text
    alert = db_session.query(StockAlert).one()
    assert (alert.email, alert.notified_at) == ("wait@example.com", None)


def test_signed_in_customer_defaults_to_account_email(client, out_of_stock, db_session):
    headers = register(client, "member@example.com")
    assert client.post("/api/v1/stock-alerts/", json={"sku_id": out_of_stock.id}, headers=headers).status_code == 201
    alert = db_session.query(StockAlert).one()
    assert alert.email == "member@example.com" and alert.user_id is not None


def test_guest_without_email_is_rejected(client, out_of_stock):
    assert client.post("/api/v1/stock-alerts/", json={"sku_id": out_of_stock.id}).status_code == 422


def test_in_stock_unknown_and_invalid_are_refused(client, sku):
    assert client.post("/api/v1/stock-alerts/", json={"sku_id": sku.id, "email": "a@example.com"}).status_code == 409
    assert client.post("/api/v1/stock-alerts/", json={"sku_id": 9999, "email": "a@example.com"}).status_code == 404
    assert client.post("/api/v1/stock-alerts/", json={"sku_id": sku.id, "email": "nope"}).status_code == 422


def test_duplicate_subscription_keeps_one_row(client, out_of_stock, db_session):
    for _ in range(3):
        assert client.post("/api/v1/stock-alerts/", json={"sku_id": out_of_stock.id, "email": "dup@example.com"}).status_code == 201
    assert db_session.query(StockAlert).count() == 1


def test_task_waits_until_stock_returns_then_sends_once(client, out_of_stock, db_session):
    client.post("/api/v1/stock-alerts/", json={"sku_id": out_of_stock.id, "email": "wait@example.com"})
    recorder = _Recorder()

    assert notify_back_in_stock(db_session, recorder) == 0  # still out of stock

    db_session.query(Inventory).filter_by(sku_id=out_of_stock.id).one().stock = 5
    db_session.commit()
    assert notify_back_in_stock(db_session, recorder) == 1
    assert recorder.sent == [("wait@example.com", "Food Container", "food-container")]
    assert db_session.query(StockAlert).one().notified_at is not None

    assert notify_back_in_stock(db_session, recorder) == 0  # never twice
    assert len(recorder.sent) == 1


def test_reserved_stock_does_not_count_as_available(client, out_of_stock, db_session):
    inv = db_session.query(Inventory).filter_by(sku_id=out_of_stock.id).one()
    inv.stock, inv.reserved = 3, 3
    db_session.commit()
    client.post("/api/v1/stock-alerts/", json={"sku_id": out_of_stock.id, "email": "w@example.com"})
    assert notify_back_in_stock(db_session, _Recorder()) == 0


def test_asking_again_after_notification_rearms_the_alert(client, out_of_stock, db_session):
    client.post("/api/v1/stock-alerts/", json={"sku_id": out_of_stock.id, "email": "again@example.com"})
    inv = db_session.query(Inventory).filter_by(sku_id=out_of_stock.id).one()
    inv.stock = 2
    db_session.commit()
    notify_back_in_stock(db_session, _Recorder())

    inv.stock = 0
    db_session.commit()
    client.post("/api/v1/stock-alerts/", json={"sku_id": out_of_stock.id, "email": "again@example.com"})
    db_session.expire_all()
    assert db_session.query(StockAlert).one().notified_at is None


def test_sending_failure_leaves_alert_pending(client, out_of_stock, db_session):
    client.post("/api/v1/stock-alerts/", json={"sku_id": out_of_stock.id, "email": "f@example.com"})
    db_session.query(Inventory).filter_by(sku_id=out_of_stock.id).one().stock = 2
    db_session.commit()

    class _Broken:
        def back_in_stock(self, *a, **k):
            raise RuntimeError("smtp down")

    assert notify_back_in_stock(db_session, _Broken()) == 0
    assert db_session.query(StockAlert).one().notified_at is None
