from decimal import Decimal
from uuid import uuid4

from app.models.order import Order
from app.services.payment.base import PaymentGatewayBase


class StubPaymentGateway(PaymentGatewayBase):
    """Placeholder until a real payment provider is chosen (PRD section 13).
    Always succeeds — for MVP testing only, never treat as a real integration."""

    def create_intent(self, order: Order) -> str:
        return f"stub-{uuid4().hex[:12]}"

    def confirm(self, reference: str) -> bool:
        return True

    def refund(self, order: Order, amount: Decimal) -> str:
        return f"stub-refund-{uuid4().hex[:12]}"
