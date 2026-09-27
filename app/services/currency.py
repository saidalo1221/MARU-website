from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exchange_rate import ExchangeRate

BASE_CURRENCY = "USD"


class CurrencyError(Exception):
    """Raised when no exchange rate is configured for a requested currency."""


def get_rate_to_usd(db: Session, currency: str) -> Decimal:
    """Units of `currency` per 1 USD, e.g. 12500 for UZS."""
    if currency == BASE_CURRENCY:
        return Decimal("1")

    rate = db.execute(select(ExchangeRate).where(ExchangeRate.currency == currency)).scalar_one_or_none()
    if rate is None:
        raise CurrencyError(f"No exchange rate configured for {currency}")
    return rate.units_per_usd


def convert_amount(db: Session, amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
    if from_currency == to_currency:
        return amount

    usd_amount = amount / get_rate_to_usd(db, from_currency)
    converted = usd_amount * get_rate_to_usd(db, to_currency)
    return converted.quantize(Decimal("0.01"))
