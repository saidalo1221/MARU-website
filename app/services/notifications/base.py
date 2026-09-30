from abc import ABC, abstractmethod

from app.models.order import Order
from app.models.shipment import Shipment


class NotificationBase(ABC):
    """Boundary for order notifications (PRD section 38: email/SMS/WhatsApp/
    Telegram). No provider has been chosen yet."""

    @abstractmethod
    def order_created(self, order: Order) -> None: ...

    @abstractmethod
    def order_status_changed(self, order: Order, old_status: str, new_status: str) -> None: ...

    @abstractmethod
    def shipment_updated(self, order: Order, shipment: Shipment) -> None: ...
