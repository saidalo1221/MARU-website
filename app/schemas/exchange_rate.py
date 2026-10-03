from typing import Optional
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExchangeRateCreate(BaseModel):
    currency: str = Field(min_length=3, max_length=3)
    # Optional: when omitted, the rate is fetched live from the FX provider
    # (app/services/fx_provider.py) instead of requiring the admin to type
    # one in. Still accepted for currencies the provider doesn't support.
    units_per_usd: Optional[Decimal] = Field(default=None, gt=0)

    @field_validator("currency")
    @classmethod
    def _not_usd(cls, v: str) -> str:
        v = v.upper()
        if v == "USD":
            raise ValueError("USD is the implicit base currency and doesn't need a rate")
        return v


class CurrencyOption(BaseModel):
    code: str
    name: str


class ExchangeRateUpdate(BaseModel):
    units_per_usd: Decimal = Field(gt=0)


class ExchangeRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    currency: str
    units_per_usd: Decimal
    updated_at: datetime
