from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.enums import OrderStatus, ShipmentStatus
from app.models.order import Order
from app.models.shipment import Shipment, ShipmentEvent
from app.models.user import User
from app.schemas.shipment import ShipmentCreate, ShipmentEventCreate
from app.services.audit import log_audit
from app.services.order_service import InvalidTransitionError, set_order_status, validate_transition


class ShipmentError(Exception):
    """Raised for shipment changes the router turns into a 409."""


# An order can only be handed to a carrier once it is packed; later states
# allow additional (split) shipments.
_SHIPPABLE_ORDER_STATUSES = {OrderStatus.PACKED, OrderStatus.SHIPPED, OrderStatus.IN_TRANSIT}

_ALLOWED_SHIPMENT_TRANSITIONS = {
    ShipmentStatus.SHIPPED: {ShipmentStatus.IN_TRANSIT, ShipmentStatus.DELIVERED, ShipmentStatus.RETURNED},
    ShipmentStatus.IN_TRANSIT: {ShipmentStatus.DELIVERED, ShipmentStatus.RETURNED},
    ShipmentStatus.DELIVERED: {ShipmentStatus.RETURNED},
    ShipmentStatus.RETURNED: set(),
}


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _target_order_status(shipments: list[Shipment]) -> Optional[OrderStatus]:
    """Order status implied by its shipments: all returned -> RETURNED; every
    live parcel delivered -> DELIVERED; anything moving or partly delivered ->
    IN_TRANSIT; otherwise SHIPPED."""
    if not shipments:
        return None
    live = [s for s in shipments if s.status != ShipmentStatus.RETURNED]
    if not live:
        return OrderStatus.RETURNED
    if all(s.status == ShipmentStatus.DELIVERED for s in live):
        return OrderStatus.DELIVERED
    if any(s.status in (ShipmentStatus.IN_TRANSIT, ShipmentStatus.DELIVERED) for s in live):
        return OrderStatus.IN_TRANSIT
    return OrderStatus.SHIPPED


def _sync_order_status(db: Session, order: Order, user: User, note: str) -> None:
    """Moves the order forward to match its shipments through the normal state
    machine (so stock release, history and audit rows still happen). A target
    the state machine rejects (e.g. order already partially refunded, or
    cancelled) is skipped rather than failing the shipment update."""
    target = _target_order_status(order.shipments)
    if target is None or target == order.status:
        return
    if order.status == OrderStatus.PACKED and target != OrderStatus.SHIPPED:
        set_order_status(db, order, OrderStatus.SHIPPED, user, note=note)
    try:
        validate_transition(order.status, target)
    except InvalidTransitionError:
        return
    set_order_status(db, order, target, user, note=note)


def _add_event(shipment: Shipment, status: ShipmentStatus, user: User, location, note, occurred_at=None) -> None:
    shipment.events.append(
        ShipmentEvent(
            status=status,
            location=location or None,
            note=note or None,
            occurred_at=occurred_at or _now(),
            created_by_user_id=user.id,
        )
    )


def create_shipment(db: Session, order: Order, data: ShipmentCreate, user: User) -> Shipment:
    if order.status not in _SHIPPABLE_ORDER_STATUSES:
        raise ShipmentError(f"Cannot ship an order in status {order.status.value}; it must be packed first")

    tracking_number = data.tracking_number
    if not tracking_number and data.carrier.strip().lower() == "maru":
        # Own delivery has no external tracking number, so issue one.
        tracking_number = f"{order.order_number}-{len(order.shipments) + 1}"

    shipment = Shipment(
        order_id=order.id,
        carrier=data.carrier,
        tracking_number=tracking_number,
        tracking_url=data.tracking_url,
        status=ShipmentStatus.SHIPPED,
        shipped_at=_now(),
        created_by_user_id=user.id,
    )
    order.shipments.append(shipment)
    _add_event(shipment, ShipmentStatus.SHIPPED, user, data.location, data.note or "Handed to carrier")
    db.flush()
    log_audit(db, user, "shipment_create", "shipment", shipment.id, None, {"order_id": order.id, "carrier": data.carrier})
    _sync_order_status(db, order, user, note=f"Shipment {shipment.id} created")
    db.commit()
    return shipment


def add_shipment_event(db: Session, order: Order, shipment: Shipment, data: ShipmentEventCreate, user: User) -> Shipment:
    if data.status != shipment.status and data.status not in _ALLOWED_SHIPMENT_TRANSITIONS[shipment.status]:
        raise ShipmentError(f"Cannot move shipment from {shipment.status.value} to {data.status.value}")

    if data.status == ShipmentStatus.DELIVERED and shipment.delivered_at is None:
        shipment.delivered_at = data.occurred_at or _now()
    old = shipment.status
    shipment.status = data.status
    _add_event(shipment, data.status, user, data.location, data.note, data.occurred_at)
    db.flush()
    log_audit(db, user, "shipment_event", "shipment", shipment.id, {"status": old.value}, {"status": data.status.value})
    _sync_order_status(db, order, user, note=f"Shipment {shipment.id}: {data.status.value}")
    db.commit()
    return shipment


def find_order_shipment(order: Order, shipment_id: int) -> Optional[Shipment]:
    return next((s for s in order.shipments if s.id == shipment_id), None)
