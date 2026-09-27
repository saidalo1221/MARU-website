import base64
from decimal import Decimal

from app.config import settings
from app.models.order import Order
from app.services.payment.base import PaymentGatewayBase
from app.services.payment.errors import PaymentConfigError, RefundNotSupportedError


class PaymePaymentGateway(PaymentGatewayBase):
    """Real Payme integration (PRD section 13, Uzbekistan local payment).

    Unlike Stripe/PayPal, Payme's protocol is inverted: after the customer is
    redirected to the checkout URL this returns and pays, PAYME's server
    calls OUR merchant webhook (POST /payments/payme/webhook, see
    app/routers/payment_webhooks.py) to create/perform/cancel the
    transaction — this class never calls out to Payme itself. confirm()
    can't do anything meaningful under that model and always returns False;
    the webhook updates order.status directly instead.

    WRITTEN FROM THE DOCUMENTED PROTOCOL (https://developer.help.paycom.uz/),
    NOT VERIFIED against a live Payme sandbox account — there were no test
    credentials available while building this. Get a test merchant account
    from https://merchant.payme.uz, point PAYME_CHECKOUT_URL at
    checkout.test.paycom.uz, and run a full pay -> webhook -> order-paid
    cycle before processing real payments. Re-check the error codes in
    payment_webhooks.py against your merchant cabinet's current docs too."""

    def create_intent(self, order: Order) -> str:
        if not settings.PAYME_MERCHANT_ID:
            raise PaymentConfigError("PAYME_MERCHANT_ID is not configured")

        amount_tiyin = int(order.total_amount * 100)
        params = f"m={settings.PAYME_MERCHANT_ID};ac.order_id={order.id};a={amount_tiyin}"
        encoded = base64.b64encode(params.encode()).decode()
        return f"{settings.PAYME_CHECKOUT_URL}/{encoded}"

    def confirm(self, reference: str) -> bool:
        return False

    def refund(self, order: Order, amount: Decimal) -> str:
        """Payme's CancelTransaction is a *merchant-inbound* webhook method
        (Payme calls us — see app/routers/payment_webhooks.py), not something
        this app can call outbound on Payme to force a refund; no such
        merchant API endpoint was documented/verified when this was written.
        Issue the refund from the Payme merchant cabinet instead."""
        raise RefundNotSupportedError(
            "Payme refunds must be issued manually from the Payme merchant cabinet; "
            "no verified outbound refund API is wired up."
        )
