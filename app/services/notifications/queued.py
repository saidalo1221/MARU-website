"""Order and shipment emails that can run in the background (PRD ТЗ№3 §88: the checkout must
not wait for SMTP). Same methods as EmailNotifier; with JOBS_ASYNC=true they only enqueue a job,
which app/tasks/worker.py turns into the email (retried with backoff, dead-lettered when it keeps
failing). With JOBS_ASYNC=false they send inline as before."""

from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.order import Order
from app.models.shipment import Shipment
from app.services.jobs import PermanentJobError, enqueue, job_handler
from app.services.notifications.email import EmailNotifier


class QueuedNotifier:
    def __init__(self) -> None:
        self._inline = EmailNotifier()

    def _queue(self, db: Optional[Session]) -> bool:
        return bool(settings.JOBS_ASYNC and db is not None)

    def order_created(self, order: Order, db: Optional[Session] = None) -> None:
        if self._queue(db):
            enqueue(db, "notify.order_created", {"order_id": order.id}, dedupe_key=f"order_created:{order.id}")
        else:
            self._inline.order_created(order, db=db)

    def order_status_changed(self, order: Order, old_status: str, new_status: str, db: Optional[Session] = None) -> None:
        if self._queue(db):
            enqueue(
                db, "notify.order_status_changed",
                {"order_id": order.id, "old_status": old_status, "new_status": new_status},
                dedupe_key=f"order_status:{order.id}:{old_status}:{new_status}",
            )
        else:
            self._inline.order_status_changed(order, old_status, new_status, db=db)

    def shipment_updated(self, order: Order, shipment: Shipment, db: Optional[Session] = None) -> None:
        if self._queue(db):
            enqueue(
                db, "notify.shipment_updated", {"order_id": order.id, "shipment_id": shipment.id},
                dedupe_key=f"shipment:{shipment.id}:{shipment.status.value}",
            )
        else:
            self._inline.shipment_updated(order, shipment, db=db)


def _order(db: Session, order_id: int) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise PermanentJobError(f"Order {order_id} no longer exists")
    return order


@job_handler("notify.order_created")
def _send_order_created(db: Session, payload: dict) -> None:
    EmailNotifier(raise_errors=True).order_created(_order(db, payload["order_id"]), db=db)


@job_handler("notify.order_status_changed")
def _send_order_status_changed(db: Session, payload: dict) -> None:
    EmailNotifier(raise_errors=True).order_status_changed(
        _order(db, payload["order_id"]), payload["old_status"], payload["new_status"], db=db
    )


@job_handler("notify.shipment_updated")
def _send_shipment_updated(db: Session, payload: dict) -> None:
    order = _order(db, payload["order_id"])
    shipment = db.get(Shipment, payload["shipment_id"])
    if shipment is None:
        raise PermanentJobError(f"Shipment {payload['shipment_id']} no longer exists")
    EmailNotifier(raise_errors=True).shipment_updated(order, shipment, db=db)
