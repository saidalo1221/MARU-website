"""PRD ТЗ№3 §31 / ТЗ№4 §23: every order has payment rows whose status follows the order."""

from decimal import Decimal

from app.models.enums import OrderStatus, PaymentStatus
from app.models.payment import Payment
from app.schemas.order import CheckoutRequest
from app.services.order_service import create_order, set_order_status
from conftest import CHECKOUT_PAYLOAD
from test_orders_reservation import _cart_with


def _order(db_session, sku, qty=1):
    order = create_order(db_session, _cart_with(db_session, sku, qty), CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()
    return order


def _rows(db_session, order):
    db_session.expire_all()
    return db_session.query(Payment).filter_by(order_id=order.id).order_by(Payment.id).all()


def test_checkout_creates_a_created_payment_for_the_order_total(db_session, sku):
    order = _order(db_session, sku, 2)
    (p,) = _rows(db_session, order)
    assert p.status == PaymentStatus.CREATED and order.payment_status == PaymentStatus.CREATED
    assert p.amount == order.total_amount and p.currency == order.currency
    assert p.provider == order.payment_method and p.idempotency_key == f"order-{order.id}-1"


def test_failed_then_retried_then_paid_keeps_every_attempt(db_session, sku):
    order = _order(db_session, sku)
    set_order_status(db_session, order, OrderStatus.PAYMENT_PENDING, None)
    assert order.payment_status == PaymentStatus.PENDING
    set_order_status(db_session, order, OrderStatus.PAYMENT_FAILED, None)
    assert order.payment_status == PaymentStatus.FAILED

    set_order_status(db_session, order, OrderStatus.PAYMENT_PENDING, None)  # retry = a new attempt
    set_order_status(db_session, order, OrderStatus.PAID, None)
    first, second = _rows(db_session, order)
    assert (first.status, second.status) == (PaymentStatus.FAILED, PaymentStatus.PAID)
    assert second.paid_at is not None and first.paid_at is None
    assert second.idempotency_key == f"order-{order.id}-2"
    assert order.payment_status == PaymentStatus.PAID


def test_cancel_unpaid_and_refunds(db_session, sku):
    unpaid = _order(db_session, sku)
    set_order_status(db_session, unpaid, OrderStatus.CANCELLED, None)
    assert unpaid.payment_status == PaymentStatus.CANCELLED

    paid = _order(db_session, sku)
    set_order_status(db_session, paid, OrderStatus.PAID, None)
    set_order_status(db_session, paid, OrderStatus.PARTIALLY_REFUNDED, None)
    assert paid.payment_status == PaymentStatus.PARTIALLY_REFUNDED
    set_order_status(db_session, paid, OrderStatus.REFUNDED, None)
    (p,) = _rows(db_session, paid)
    assert p.status == PaymentStatus.REFUNDED and p.amount == paid.total_amount and p.paid_at is not None


def test_cancelling_a_paid_order_does_not_pretend_the_money_went_back(db_session, sku):
    order = _order(db_session, sku)
    set_order_status(db_session, order, OrderStatus.PAID, None)
    set_order_status(db_session, order, OrderStatus.CANCELLED, None)
    assert order.payment_status == PaymentStatus.PAID  # a refund is what changes it


def test_stripe_intent_id_is_recorded_but_never_the_secret(db_session, sku):
    order = _order(db_session, sku)
    order.payment_method = "stripe"
    order.payment_reference = "pi_123_secret_abc"
    db_session.commit()
    set_order_status(db_session, order, OrderStatus.PAID, None)
    (p,) = _rows(db_session, order)
    assert p.provider_transaction_id == "pi_123"


def test_order_api_and_admin_payments_endpoint_expose_status(client, db_session, sku):
    from app.models.enums import UserRole
    from conftest import login, make_admin

    order = _order(db_session, sku)
    r = client.get(f"/api/v1/orders/{order.id}", headers={"X-Order-Token": order.guest_order_token})
    assert r.json()["payment_status"] == "created"

    make_admin(db_session, "sales@example.com", UserRole.SALES_MANAGER)
    h = login(client, "sales@example.com")
    rows = client.get(f"/api/v1/admin/orders/{order.id}/payments", headers=h).json()
    assert [(x["status"], Decimal(x["amount"])) for x in rows] == [("created", order.total_amount)]
