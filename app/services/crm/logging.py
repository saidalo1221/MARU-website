import logging

from app.models.order import Order
from app.services.crm.base import CRMBase

logger = logging.getLogger("maru.crm")


class LoggingCRMConnector(CRMBase):
    """Placeholder until a real CRM provider is chosen (PRD section 26).
    Logs the exact payload a real integration would send; sends nothing."""

    def push_order(self, order: Order) -> None:
        logger.info(
            "crm.push order_number=%s client=%s %s email=%s phone=%s country=%s "
            "items=%d total=%s %s delivery=%s source=%s payment_method=%s status=%s",
            order.order_number,
            order.first_name,
            order.last_name,
            order.email,
            order.phone,
            order.country,
            len(order.items),
            order.total_amount,
            order.currency,
            order.delivery_amount,
            order.source,
            order.payment_method,
            order.status.value,
        )
