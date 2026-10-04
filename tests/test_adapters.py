"""PRD ТЗ№4 §1-5: adapter registry, external id mapping, integration events."""

import pytest

from app.models.job import Job
from app.services import jobs
from app.services.integrations import adapters, events
from conftest import CHECKOUT_PAYLOAD
from test_orders_reservation import _cart_with
from app.schemas.order import CheckoutRequest
from app.services.order_service import create_order


@pytest.fixture(autouse=True)
def _clean_registry():
    saved = dict(adapters._REGISTERED)
    adapters._REGISTERED.clear()
    yield
    adapters._REGISTERED.clear()
    adapters._REGISTERED.update(saved)


def test_unconfigured_kinds_are_safe_noops():
    assert adapters.get_adapter("erp").push_order(object()) is None
    assert adapters.get_adapter("sms").send("+998900000000", "hi") is False
    assert not adapters.is_configured("erp")
    with pytest.raises(ValueError):
        adapters.register_adapter("fax", object())


def test_external_id_mapping_round_trip(db_session):
    adapters.set_external_id(db_session, "erp", "order", 5, "1C-77")
    adapters.set_external_id(db_session, "erp", "order", 5, "1C-78")  # updates, no duplicate
    db_session.commit()
    assert adapters.get_external_id(db_session, "erp", "order", 5) == "1C-78"
    assert adapters.find_internal_id(db_session, "erp", "order", "1C-78") == 5
    assert adapters.find_internal_id(db_session, "erp", "order", "nope") is None


def test_event_reaches_configured_erp_and_saves_its_id(db_session, sku):
    order = create_order(db_session, _cart_with(db_session, sku, 1), CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()

    assert events.emit(db_session, events.ORDER_PAID, order) is None  # nobody listening: nothing queued
    assert db_session.query(Job).count() == 0

    class FakeERP(adapters.ERPAdapter):
        def push_order(self, o): return f"1C-{o.id}"
        def push_stock_levels(self, rows): pass

    adapters.register_adapter("erp", FakeERP())
    events.emit(db_session, events.ORDER_PAID, order, commit=True)
    assert jobs.run_pending(db_session, "w") == 1
    assert adapters.get_external_id(db_session, "erp", "order", order.id) == f"1C-{order.id}"


def test_erp_failure_is_isolated_from_the_order_and_retried(db_session, sku):
    """PRD ТЗ№4 §78/§98: a broken ERP must not touch the order; its job is retried later."""
    order = create_order(db_session, _cart_with(db_session, sku, 1), CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()

    class BrokenERP(adapters.ERPAdapter):
        def push_order(self, o): raise ConnectionError("1C is down")
        def push_stock_levels(self, rows): pass

    adapters.register_adapter("erp", BrokenERP())
    from app.models.enums import OrderStatus
    from app.services.order_service import set_order_status

    set_order_status(db_session, order, OrderStatus.PAYMENT_PENDING, None)
    set_order_status(db_session, order, OrderStatus.PAID, None)  # must not raise
    assert order.status == OrderStatus.PAID
    jobs.run_pending(db_session, "w")
    job = db_session.query(Job).one()
    assert job.status == "pending" and job.attempts == 1 and "1C is down" in job.last_error
