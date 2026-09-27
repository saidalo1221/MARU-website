from abc import ABC, abstractmethod
from decimal import Decimal

from app.models.order import Order


class PaymentGatewayBase(ABC):
    """Boundary PRD section 13 requires: a swappable payment module so a real
    local (Uzbekistan) or international provider can be dropped in later
    without changing checkout. No provider has been chosen yet."""

    @abstractmethod
    def create_intent(self, order: Order) -> str:
        """Return a provider-side payment reference/intent id for this order."""

    @abstractmethod
    def confirm(self, reference: str) -> bool:
        """Return True if the payment referenced is confirmed as paid."""

    @abstractmethod
    def refund(self, order: Order, amount: Decimal) -> str:
        """Ask the provider to refund `amount` of the payment referenced by
        `order.payment_reference`. Returns the provider's refund id.
        Raises RefundNotSupportedError if this gateway has no verified
        outbound refund API, or PaymentProviderError if the provider itself
        rejects the request."""
