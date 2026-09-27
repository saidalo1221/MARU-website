import logging

from app.models.order import Order
from app.services.notifications.base import NotificationBase

logger = logging.getLogger("maru.notifications")


class LoggingNotifier(NotificationBase):
    """Placeholder until a real email/SMS/WhatsApp/Telegram provider is
    chosen (PRD section 38). Logs intent only; sends nothing."""

    def order_created(self, order: Order) -> None:
        logger.info(
            "order.created order_number=%s email=%s total=%s %s",
            order.order_number,
            order.email,
            order.total_amount,
            order.currency,
        )

    def order_status_changed(self, order: Order, old_status: str, new_status: str) -> None:
        logger.info("order.status_changed order_number=%s %s -> %s", order.order_number, old_status, new_status)
