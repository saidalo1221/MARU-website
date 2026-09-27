from decimal import Decimal

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.exchange_rate import ExchangeRate

# Currencies this storefront actually offers (frontend/src/components/CurrencySwitcher.jsx).
# USD is the implicit base (ExchangeRate never stores a USD row) and is
# excluded here even though the provider returns a rate for it too.
TRACKED_CURRENCIES = ("UZS", "EUR", "KZT", "AED")


class FxProviderError(Exception):
    """Raised when the exchange rate provider isn't configured, can't be
    reached, or returns something unexpected. Callers should not let this
    break checkout — stale admin-maintained rates are safer than none."""


def fetch_latest_rates() -> dict[str, Decimal]:
    """One call to exchangerate-api.com's /latest/USD endpoint (free tier:
    1,500 requests/month) — callers must not invoke this per-request; see
    app/tasks/sync_exchange_rates.py for the intended (daily, scheduled)
    call pattern. Returns {currency: units_per_usd} for TRACKED_CURRENCIES."""
    if not settings.EXCHANGERATE_API_KEY:
        raise FxProviderError("EXCHANGERATE_API_KEY is not configured")

    url = f"{settings.EXCHANGERATE_API_BASE}/{settings.EXCHANGERATE_API_KEY}/latest/USD"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        body = response.json()
    except requests.RequestException as exc:
        raise FxProviderError(f"Failed to reach exchange rate provider: {exc}") from exc

    if body.get("result") != "success":
        raise FxProviderError(f"Exchange rate provider returned an error: {body.get('error-type', body)}")

    rates = body.get("conversion_rates", {})
    missing = [c for c in TRACKED_CURRENCIES if c not in rates]
    if missing:
        raise FxProviderError(f"Provider response is missing rates for: {missing}")

    return {currency: Decimal(str(rates[currency])) for currency in TRACKED_CURRENCIES}


def sync_exchange_rates(db: Session) -> int:
    """Upserts ExchangeRate rows for TRACKED_CURRENCIES from the live feed.
    Returns the number of currencies updated. Raises FxProviderError/
    PaymentConfigError on failure — callers (the scheduled task, the admin
    sync endpoint) decide how to surface that; this never silently no-ops."""
    rates = fetch_latest_rates()

    updated = 0
    for currency, units_per_usd in rates.items():
        existing = db.execute(select(ExchangeRate).where(ExchangeRate.currency == currency)).scalar_one_or_none()
        if existing is None:
            db.add(ExchangeRate(currency=currency, units_per_usd=units_per_usd))
        else:
            existing.units_per_usd = units_per_usd
        updated += 1

    db.commit()
    return updated
