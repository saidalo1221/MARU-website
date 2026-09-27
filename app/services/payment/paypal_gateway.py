from decimal import Decimal

import requests

from app.config import settings
from app.models.order import Order
from app.services.payment.base import PaymentGatewayBase
from app.services.payment.errors import PaymentConfigError, PaymentProviderError


class PayPalPaymentGateway(PaymentGatewayBase):
    """Real PayPal Orders v2 integration (PRD section 13, international
    payments) via plain REST calls (no PayPal SDK, to avoid an extra
    dependency). Requires PAYPAL_CLIENT_ID/PAYPAL_CLIENT_SECRET in .env.
    create_intent() creates a PayPal order and returns its id; the frontend
    must redirect the buyer to the "approve" link from PayPal's response
    before confirm() (which attempts to capture) can succeed.
    PAYPAL_API_BASE defaults to the sandbox — switch to
    https://api-m.paypal.com in .env once you're ready to go live."""

    def _access_token(self) -> str:
        if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
            raise PaymentConfigError("PAYPAL_CLIENT_ID/PAYPAL_CLIENT_SECRET are not configured")

        response = requests.post(
            f"{settings.PAYPAL_API_BASE}/v1/oauth2/token",
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
            data={"grant_type": "client_credentials"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def create_intent(self, order: Order) -> str:
        token = self._access_token()
        response = requests.post(
            f"{settings.PAYPAL_API_BASE}/v2/checkout/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "reference_id": order.order_number,
                        "amount": {"currency_code": order.currency, "value": str(order.total_amount)},
                    }
                ],
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["id"]

    def confirm(self, reference: str) -> bool:
        if not reference:
            return False
        token = self._access_token()
        response = requests.post(
            f"{settings.PAYPAL_API_BASE}/v2/checkout/orders/{reference}/capture",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if response.status_code >= 400:
            return False
        return response.json().get("status") == "COMPLETED"

    def refund(self, order: Order, amount: Decimal) -> str:
        """PayPal Orders v2 stores the *order* id in order.payment_reference,
        but refunds are issued against a *capture* id
        (https://developer.paypal.com/docs/api/payments/v2/#captures_refund),
        so the captured PayPal order is looked up first. Documented and
        stable API, but NOT verified against a live/sandbox PayPal account
        (no test credentials were available when this was written)."""
        reference = order.payment_reference or ""
        if not reference:
            raise PaymentProviderError("Cannot refund: no PayPal order id in order.payment_reference")

        token = self._access_token()
        order_response = requests.get(
            f"{settings.PAYPAL_API_BASE}/v2/checkout/orders/{reference}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if order_response.status_code >= 400:
            raise PaymentProviderError(f"Could not look up PayPal order {reference}: {order_response.text}")

        try:
            capture_id = order_response.json()["purchase_units"][0]["payments"]["captures"][0]["id"]
        except (KeyError, IndexError) as exc:
            raise PaymentProviderError(f"PayPal order {reference} has no capture to refund") from exc

        refund_response = requests.post(
            f"{settings.PAYPAL_API_BASE}/v2/payments/captures/{capture_id}/refund",
            headers={"Authorization": f"Bearer {token}"},
            json={"amount": {"currency_code": order.currency, "value": str(amount)}},
            timeout=10,
        )
        if refund_response.status_code >= 400:
            raise PaymentProviderError(f"PayPal refund failed: {refund_response.text}")
        return refund_response.json()["id"]
