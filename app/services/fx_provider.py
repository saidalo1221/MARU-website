from typing import Optional
import time
from decimal import Decimal

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.exchange_rate import ExchangeRate

# Currencies offered out of the box before an admin adds any more (used only
# to seed a completely empty table — see sync_exchange_rates below). Once an
# admin adds a currency (app/routers/admin_exchange_rates.py), it's tracked
# dynamically from then on: sync just refreshes whatever ExchangeRate rows
# already exist, no hardcoded list to keep in sync with the admin panel.
DEFAULT_BOOTSTRAP_CURRENCIES = ("UZS", "EUR", "KZT", "AED")

_codes_cache: Optional[list[dict[str, str]]] = None
_codes_cache_at: float = 0.0
_CODES_CACHE_TTL_SECONDS = 24 * 3600


class FxProviderError(Exception):
    """Raised when the exchange rate provider isn't configured, can't be
    reached, or returns something unexpected. Callers should not let this
    break checkout — stale admin-maintained rates are safer than none."""


def fetch_all_rates() -> dict[str, Decimal]:
    """One call to exchangerate-api.com's /latest/USD endpoint (free tier:
    1,500 requests/month) — callers must not invoke this per-request. Returns
    {currency: units_per_usd} for every currency the provider supports
    (excluding USD itself, the implicit base)."""
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
    return {currency: Decimal(str(rate)) for currency, rate in rates.items() if currency != "USD"}


def fetch_rate_for_currency(currency: str) -> Decimal:
    """Live rate for one currency, e.g. when an admin adds it (see
    admin_exchange_rates.py's create_exchange_rate)."""
    rates = fetch_all_rates()
    if currency not in rates:
        raise FxProviderError(f"Exchange rate provider has no rate for {currency}")
    return rates[currency]


def fetch_supported_currencies() -> list[dict[str, str]]:
    """[{code, name}, ...] for every currency the provider supports, via its
    /codes endpoint — backs the searchable currency picker in the admin
    panel (app/routers/admin_exchange_rates.py). Cached in-process since the
    list essentially never changes and this must not count against the
    provider's per-minute/per-month request budget on every keystroke."""
    global _codes_cache, _codes_cache_at

    if _codes_cache is not None and time.monotonic() - _codes_cache_at < _CODES_CACHE_TTL_SECONDS:
        return _codes_cache

    if not settings.EXCHANGERATE_API_KEY:
        raise FxProviderError("EXCHANGERATE_API_KEY is not configured")

    url = f"{settings.EXCHANGERATE_API_BASE}/{settings.EXCHANGERATE_API_KEY}/codes"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        body = response.json()
    except requests.RequestException as exc:
        raise FxProviderError(f"Failed to reach exchange rate provider: {exc}") from exc

    if body.get("result") != "success":
        raise FxProviderError(f"Exchange rate provider returned an error: {body.get('error-type', body)}")

    codes = [
        {"code": code, "name": name}
        for code, name in body.get("supported_codes", [])
        if code != "USD"
    ]
    _codes_cache = codes
    _codes_cache_at = time.monotonic()
    return codes


def sync_exchange_rates(db: Session) -> int:
    """Refreshes every currency an admin has already added (ExchangeRate
    rows), plus bootstraps DEFAULT_BOOTSTRAP_CURRENCIES the first time this
    runs against a completely empty table. Returns the number of currencies
    updated. Raises FxProviderError on failure — callers (the scheduled
    task, the admin sync endpoint) decide how to surface that; this never
    silently no-ops."""
    rates = fetch_all_rates()

    existing = list(db.execute(select(ExchangeRate)).scalars().all())
    tracked = {row.currency for row in existing} or set(DEFAULT_BOOTSTRAP_CURRENCIES)

    updated = 0
    by_currency = {row.currency: row for row in existing}
    for currency in tracked:
        if currency not in rates:
            continue
        row = by_currency.get(currency)
        if row is None:
            db.add(ExchangeRate(currency=currency, units_per_usd=rates[currency]))
        else:
            row.units_per_usd = rates[currency]
        updated += 1

    db.commit()
    return updated
