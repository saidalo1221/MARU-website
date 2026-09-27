from decimal import Decimal, ROUND_HALF_UP

import requests

from app.config import settings
from app.models.order import Order
from app.services.payment.base import PaymentGatewayBase
from app.services.payment.errors import PaymentConfigError, PaymentProviderError

_API_BASE = "https://api.stripe.com/v1"


class StripePaymentGateway(PaymentGatewayBase):
    """Real Stripe PaymentIntents integration (PRD section 13, international
    payments) via Stripe's plain REST API (no stripe-python SDK, to avoid
    adding a dependency beyond `requests`). Requires STRIPE_SECRET_KEY in
    .env. The reference returned by create_intent() is the client_secret the
    frontend needs to complete the payment with Stripe.js; confirm() polls
    the PaymentIntent's status server-side rather than trusting a webhook, so
    no STRIPE_WEBHOOK_SECRET wiring is required to make checkout work (add a
    /payments/stripe/webhook endpoint later if you want event-driven
    confirmation instead of polling)."""

    def _auth(self) -> tuple[str, str]:
        if not settings.STRIPE_SECRET_KEY:
            raise PaymentConfigError("STRIPE_SECRET_KEY is not configured")
        return (settings.STRIPE_SECRET_KEY, "")

    def create_intent(self, order: Order) -> str:
        amount_minor = int((order.total_amount * 100).to_integral_value(rounding=ROUND_HALF_UP))
        response = requests.post(
            f"{_API_BASE}/payment_intents",
            auth=self._auth(),
            data={
                "amount": amount_minor,
                "currency": order.currency.lower(),
                "receipt_email": order.email,
                "metadata[order_number]": order.order_number,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["client_secret"]

    def confirm(self, reference: str) -> bool:
        if not reference or "_secret_" not in reference:
            return False
        payment_intent_id = reference.split("_secret_")[0]
        response = requests.get(f"{_API_BASE}/payment_intents/{payment_intent_id}", auth=self._auth(), timeout=10)
        response.raise_for_status()
        return response.json().get("status") == "succeeded"

    def refund(self, order: Order, amount: Decimal) -> str:
        """Stripe's Refunds API (https://stripe.com/docs/api/refunds/create)
        — documented and stable, but NOT verified against a live/sandbox
        Stripe account (no test credentials were available when this was
        written); confirm a real refund cycle before relying on it."""
        reference = order.payment_reference or ""
        if "_secret_" not in reference:
            raise PaymentProviderError(f"Cannot refund: no Stripe PaymentIntent id in reference {reference!r}")
        payment_intent_id = reference.split("_secret_")[0]
        amount_minor = int((amount * 100).to_integral_value(rounding=ROUND_HALF_UP))
        response = requests.post(
            f"{_API_BASE}/refunds",
            auth=self._auth(),
            data={"payment_intent": payment_intent_id, "amount": amount_minor},
            timeout=10,
        )
        if response.status_code >= 400:
            raise PaymentProviderError(f"Stripe refund failed: {response.text}")
        return response.json()["id"]
