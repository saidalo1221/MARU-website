"""Stock reservation at order creation, its TTL, and the state-machine
transitions that release/re-reserve it (PRD ТЗ№3 §19/§60/§63/§68)."""

from datetime import datetime, timedelta, timezone

from app.models.enums import OrderStatus
from app.models.inventory import Inventory
from app.schemas.order import CheckoutRequest
from app.services.order_service import (
    OrderError,
    create_order,
    expire_stale_reservations,
    set_order_status,
)
from conftest import CHECKOUT_PAYLOAD

from app.models.cart import Cart
from app.models.cart_item import CartItem


def _cart_with(db_session, sku, quantity):
    cart = Cart(token=f"tok-{sku.id}-{quantity}-{id(object())}")
    db_session.add(cart)
    db_session.flush()
    db_session.add(CartItem(cart_id=cart.id, sku_id=sku.id, quantity=quantity))
    db_session.commit()
    db_session.refresh(cart)
    return cart


def _inventory_row(db_session, sku_id):
    return db_session.query(Inventory).filter_by(sku_id=sku_id).one()


def test_checkout_reserves_stock_immediately(db_session, sku):
    cart = _cart_with(db_session, sku, 3)
    order = create_order(db_session, cart, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()

    assert order.status == OrderStatus.NEW
    assert order.reservation_expires_at is not None
    assert _inventory_row(db_session, sku.id).reserved == 3


def test_checkout_rejects_when_stock_insufficient(db_session, sku):
    cart = _cart_with(db_session, sku, 3)
    create_order(db_session, cart, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()

    cart2 = _cart_with(db_session, sku, 8)  # only 7 left
    try:
        create_order(db_session, cart2, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
        assert False, "expected OrderError for insufficient stock"
    except OrderError:
        db_session.rollback()

    assert _inventory_row(db_session, sku.id).reserved == 3


def test_payment_failed_releases_reservation(db_session, sku):
    cart = _cart_with(db_session, sku, 4)
    order = create_order(db_session, cart, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()

    set_order_status(db_session, order, OrderStatus.PAYMENT_FAILED, None, note="test")

    assert _inventory_row(db_session, sku.id).reserved == 0
    assert order.reservation_expires_at is None


def test_retry_after_payment_failed_re_reserves_stock(db_session, sku):
    cart = _cart_with(db_session, sku, 4)
    order = create_order(db_session, cart, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()
    set_order_status(db_session, order, OrderStatus.PAYMENT_FAILED, None, note="test")
    assert _inventory_row(db_session, sku.id).reserved == 0

    set_order_status(db_session, order, OrderStatus.PAYMENT_PENDING, None, note="retry")
    assert _inventory_row(db_session, sku.id).reserved == 4

    set_order_status(db_session, order, OrderStatus.PAID, None, note="paid")
    assert order.status == OrderStatus.PAID
    assert _inventory_row(db_session, sku.id).reserved == 4  # unchanged, not double-reserved


def test_ttl_expiry_cancels_order_and_releases_stock(db_session, sku):
    cart = _cart_with(db_session, sku, 5)
    order = create_order(db_session, cart, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()

    order.reservation_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    db_session.commit()

    expired_count = expire_stale_reservations(db_session)

    db_session.refresh(order)
    assert expired_count == 1
    assert order.status == OrderStatus.CANCELLED
    assert _inventory_row(db_session, sku.id).reserved == 0


def test_ttl_not_yet_reached_is_not_expired(db_session, sku):
    cart = _cart_with(db_session, sku, 2)
    order = create_order(db_session, cart, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()

    expired_count = expire_stale_reservations(db_session)

    db_session.refresh(order)
    assert expired_count == 0
    assert order.status == OrderStatus.NEW


def test_cancelled_order_releases_stock(db_session, sku):
    cart = _cart_with(db_session, sku, 6)
    order = create_order(db_session, cart, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()

    set_order_status(db_session, order, OrderStatus.CANCELLED, None, note="customer cancelled")

    assert _inventory_row(db_session, sku.id).reserved == 0


def test_invalid_transition_is_rejected(db_session, sku):
    from app.services.order_service import InvalidTransitionError, validate_transition

    try:
        validate_transition(OrderStatus.DELIVERED, OrderStatus.NEW)
        assert False, "expected InvalidTransitionError"
    except InvalidTransitionError:
        pass
