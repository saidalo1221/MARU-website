class PaymentConfigError(Exception):
    """Raised when a gateway's required settings (API keys etc.) aren't
    configured in .env yet. Routers translate this to a 503 response."""


class RefundNotSupportedError(Exception):
    """Raised by a gateway whose refund() has no verified outbound API to
    call yet (Payme/Click — see their refund() docstrings). Routers/services
    translate this to a 501/409-style response; the refund must be issued
    manually through the provider's merchant cabinet instead."""


class PaymentProviderError(Exception):
    """Raised when a gateway's refund call reaches the provider but the
    provider itself rejects or fails it."""
