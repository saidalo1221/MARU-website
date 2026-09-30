from typing import Optional
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _check_days(min_days, max_days):
    if min_days is not None and max_days is not None and min_days > max_days:
        raise ValueError("min_delivery_days cannot exceed max_delivery_days")


class ShippingRateCreate(BaseModel):
    country: str = Field(min_length=1, max_length=100, description="Country name, or '*' for any country")
    delivery_method: str = Field(min_length=1, max_length=50, description="Delivery method, or '*' for any method")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    base_fee: Decimal = Field(default=Decimal("0"), ge=0)
    per_kg_fee: Decimal = Field(default=Decimal("0"), ge=0)
    free_shipping_threshold: Optional[Decimal] = Field(default=None, gt=0)
    min_delivery_days: Optional[int] = Field(default=None, ge=0, le=365)
    max_delivery_days: Optional[int] = Field(default=None, ge=0, le=365)
    is_active: bool = True

    @model_validator(mode="after")
    def _days(self):
        _check_days(self.min_delivery_days, self.max_delivery_days)
        return self


class ShippingRateUpdate(BaseModel):
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    base_fee: Optional[Decimal] = Field(default=None, ge=0)
    per_kg_fee: Optional[Decimal] = Field(default=None, ge=0)
    free_shipping_threshold: Optional[Decimal] = Field(default=None, gt=0)
    min_delivery_days: Optional[int] = Field(default=None, ge=0, le=365)
    max_delivery_days: Optional[int] = Field(default=None, ge=0, le=365)
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def _days(self):
        _check_days(self.min_delivery_days, self.max_delivery_days)
        return self


class ShippingRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country: str
    delivery_method: str
    currency: str
    base_fee: Decimal
    per_kg_fee: Decimal
    free_shipping_threshold: Optional[Decimal]
    min_delivery_days: Optional[int]
    max_delivery_days: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ShippingEstimateOut(BaseModel):
    min_days: Optional[int] = None
    max_days: Optional[int] = None
    # In `currency`; the storefront converts for display.
    free_shipping_threshold: Optional[Decimal] = None
    currency: Optional[str] = None
