"""Internal integration events (PRD ТЗ№4 §1-5: OrderCreated, OrderPaid, ...). Code that changes an
order calls emit(); the event is queued as a background job and delivered to whichever adapters
are configured. With no connector registered nothing is queued, so this costs nothing today."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.order import Order
from app.services.integrations.adapters import get_adapter, is_configured, set_external_id
from app.services.jobs import enqueue, job_handler

ORDER_CREATED = "OrderCreated"
ORDER_PAID = "OrderPaid"
ORDER_CANCELLED = "OrderCancelled"
SHIPMENT_UPDATED = "ShipmentUpdated"

# event -> adapter kinds that care about it
_SUBSCRIBERS = {ORDER_PAID: ("erp",), ORDER_CANCELLED: ("erp",), SHIPMENT_UPDATED: ("marketplace",)}


def emit(db: Session, event: str, order: Order, commit: bool = False) -> Optional[object]:
    if not any(is_configured(kind) for kind in _SUBSCRIBERS.get(event, ())):
        return None
    return enqueue(db, "integration.event", {"event": event, "order_id": order.id},
                   dedupe_key=f"event:{event}:{order.id}", commit=commit)


@job_handler("integration.event")
def _deliver(db: Session, payload: dict) -> None:
    order = db.get(Order, payload["order_id"])
    if order is None:
        return
    if payload["event"] in (ORDER_PAID, ORDER_CANCELLED) and is_configured("erp"):
        external = get_adapter("erp").push_order(order)
        if external:
            set_external_id(db, "erp", "order", order.id, str(external))
