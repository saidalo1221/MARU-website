from decimal import Decimal

from app.config import settings
from app.models.order import Order
from app.services.payment.base import PaymentGatewayBase
from app.services.payment.errors import PaymentConfigError, RefundNotSupportedError


class ClickPaymentGateway(PaymentGatewayBase):
    """Real Click integration (PRD section 13, Uzbekistan local payment).

    Same inverted-control shape as Payme: after redirecting the customer to
    the URL this returns, CLICK's server calls OUR merchant webhook (POST
    /payments/click/webhook, see app/routers/payment_webhooks.py) with
    Prepare then Complete actions — this class never calls out to Click.
    confirm() always returns False; the webhook updates order.status.

    WRITTEN FROM THE DOCUMENTED PROTOCOL (https://docs.click.uz/), NOT
    VERIFIED against a live Click sandbox — get test credentials from Click's
    merchant cabinet and run a full pay -> webhook -> order-paid cycle
    before processing real payments."""

    def create_intent(self, order: Order) -> str:
        if not settings.CLICK_SERVICE_ID or not settings.CLICK_MERCHANT_ID:
            raise PaymentConfigError("CLICK_SERVICE_ID/CLICK_MERCHANT_ID are not configured")

        return (
            "https://my.click.uz/services/pay"
            f"?service_id={settings.CLICK_SERVICE_ID}"
            f"&merchant_id={settings.CLICK_MERCHANT_ID}"
            f"&amount={order.total_amount}"
            f"&transaction_param={order.id}"
        )

    def confirm(self, reference: str) -> bool:
        return False

    def refund(self, order: Order, amount: Decimal) -> str:
        """Same inverted-control shape as create_intent()/confirm(): Click's
        documented protocol only covers Prepare/Complete callbacks *into*
        this app. No outbound merchant refund endpoint was documented or
        verified when this was written. Issue the refund from the Click
        merchant cabinet instead."""
        raise RefundNotSupportedError(
            "Click refunds must be issued manually from the Click merchant cabinet; "
            "no verified outbound refund API is wired up."
        )
