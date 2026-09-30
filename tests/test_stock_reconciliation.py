"""Inventory.reserved drift detection and repair."""

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.enums import OrderStatus
from app.models.inventory import Inventory
from app.schemas.order import CheckoutRequest
from app.services.order_service import create_order, set_order_status
from app.services.stock_reconciliation import find_mismatches, fix_reserved_drift
from conftest import CHECKOUT_PAYLOAD


def _order(db_session, sku, quantity):
    cart = Cart(token=f"t-{id(object())}")
    db_session.add(cart)
    db_session.flush()
    db_session.add(CartItem(cart_id=cart.id, sku_id=sku.id, quantity=quantity))
    db_session.commit()
    db_session.refresh(cart)
    order = create_order(db_session, cart, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()
    return order


def _inv(db_session, sku):
    db_session.expire_all()
    return db_session.query(Inventory).filter_by(sku_id=sku.id).one()


def test_consistent_inventory_has_no_mismatches(db_session, sku):
    order = _order(db_session, sku, 3)
    assert find_mismatches(db_session) == []
    set_order_status(db_session, order, OrderStatus.CANCELLED, None)  # releases stock
    assert find_mismatches(db_session) == []


def test_drift_is_detected_and_fixed(db_session, sku):
    _order(db_session, sku, 3)
    inv = _inv(db_session, sku)
    inv.reserved = 7  # simulates a missed decrement/increment
    db_session.commit()

    (m,) = find_mismatches(db_session)
    assert (m.problem, m.reserved, m.expected_reserved) == ("reserved_drift", 7, 3)

    assert fix_reserved_drift(db_session) == 1
    assert _inv(db_session, sku).reserved == 3
    assert find_mismatches(db_session) == []


def test_leaked_reservation_with_no_order_is_found(db_session, sku):
    inv = _inv(db_session, sku)
    inv.reserved = 4
    db_session.commit()
    (m,) = find_mismatches(db_session)
    assert (m.reserved, m.expected_reserved) == (4, 0)
    fix_reserved_drift(db_session)
    assert _inv(db_session, sku).reserved == 0


def test_oversold_is_reported_but_never_auto_fixed(db_session, sku):
    _order(db_session, sku, 3)
    inv = _inv(db_session, sku)
    inv.stock = 2  # physical stock below what orders hold
    db_session.commit()
    (m,) = find_mismatches(db_session)
    assert m.problem == "oversold"
    assert fix_reserved_drift(db_session) == 0
    assert _inv(db_session, sku).reserved == 3


def test_cancelled_orders_hold_nothing(db_session, sku):
    order = _order(db_session, sku, 2)
    set_order_status(db_session, order, OrderStatus.CANCELLED, None)
    inv = _inv(db_session, sku)
    inv.reserved = 2  # stale counter for an order that no longer holds stock
    db_session.commit()
    assert [m.problem for m in find_mismatches(db_session)] == ["reserved_drift"]
