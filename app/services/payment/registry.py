from typing import Optional

from app.services.payment.base import PaymentGatewayBase
from app.services.payment.click import ClickPaymentGateway
from app.services.payment.payme import PaymePaymentGateway
from app.services.payment.paypal_gateway import PayPalPaymentGateway
from app.services.payment.stripe_gateway import StripePaymentGateway
from app.config import settings
from app.services.payment.errors import PaymentConfigError

_GATEWAYS: dict[str, PaymentGatewayBase] = {
    "payme": PaymePaymentGateway(),
    "click": ClickPaymentGateway(),
    "stripe": StripePaymentGateway(),
    "paypal": PayPalPaymentGateway(),
}

# Uzum Pay is deliberately absent.  Its merchant API contract, signing rules,
# and credentials have not been supplied; do not invent an integration from
# consumer-facing documentation.  Add it here only after those materials are
# provided and verified in its sandbox.
UZUM_PAY_STATUS = "blocked_pending_merchant_api_docs"


_METHOD_METADATA = {
    "payme": {"display_name": "Payme", "reference_kind": "redirect_url"},
    "click": {"display_name": "Click", "reference_kind": "redirect_url"},
    "stripe": {"display_name": "Stripe", "reference_kind": "client_secret"},
    "paypal": {"display_name": "PayPal", "reference_kind": "provider_order_id"},
}


def _is_configured(payment_method: str) -> bool:
    return {
        "payme": bool(settings.PAYME_MERCHANT_ID and settings.PAYME_KEY),
        "click": bool(settings.CLICK_SERVICE_ID and settings.CLICK_MERCHANT_ID and settings.CLICK_SECRET_KEY),
        "stripe": bool(settings.STRIPE_SECRET_KEY),
        "paypal": bool(settings.PAYPAL_CLIENT_ID and settings.PAYPAL_CLIENT_SECRET),
    }[payment_method]


# Local gateways only settle in their home market, so they are not offered
# elsewhere (PRD ТЗ№2 §37: do not show methods unavailable in the buyer's region).
_LOCAL_ONLY_COUNTRY = {"payme": "Uzbekistan", "click": "Uzbekistan"}


def method_available_in_country(payment_method: str, country: Optional[str]) -> bool:
    """True when the method may be used for a delivery to `country` (or no country is known yet)."""
    home = _LOCAL_ONLY_COUNTRY.get(payment_method.lower())
    return home is None or not country or country.strip().lower() == home.lower()


def list_payment_methods(country: Optional[str] = None) -> list[dict]:
    methods = []
    for method, metadata in _METHOD_METADATA.items():
        in_region = method_available_in_country(method, country)
        enabled = _is_configured(method) and in_region
        methods.append(
            {
                "id": method,
                **metadata,
                "enabled": enabled,
                "reason": None if enabled else (
                    "Merchant configuration is incomplete" if in_region else "Not available in this country"
                ),
            }
        )
    methods.append(
        {
            "id": "uzum_pay",
            "display_name": "Uzum Pay",
            "enabled": False,
            "reference_kind": None,
            "reason": "Merchant API documentation and sandbox credentials are required",
        }
    )
    return methods


def ensure_payment_method_configured(payment_method: str) -> None:
    if payment_method not in _GATEWAYS or not _is_configured(payment_method):
        raise PaymentConfigError(f"{payment_method} is not available")


def payment_reference_kind(payment_method: str) -> str:
    return _METHOD_METADATA[payment_method]["reference_kind"]


def get_payment_gateway(payment_method: str) -> PaymentGatewayBase:
    gateway = _GATEWAYS.get(payment_method.lower())
    if gateway is None:
        raise ValueError(f"Unsupported payment method: {payment_method}")
    return gateway
