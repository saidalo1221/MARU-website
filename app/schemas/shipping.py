from typing import Optional
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ShippingRateCreate(BaseModel):
    country: str = Field(min_length=1, max_length=100, description="Country name, or '*' for any country")
    delivery_method: str = Field(min_length=1, max_length=50, description="Delivery method, or '*' for any method")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    base_fee: Decimal = Field(default=Decimal("0"), ge=0)
    per_kg_fee: Decimal = Field(default=Decimal("0"), ge=0)
    is_active: bool = True


class ShippingRateUpdate(BaseModel):
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    base_fee: Optional[Decimal] = Field(default=None, ge=0)
    per_kg_fee: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class ShippingRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country: str
    delivery_method: str
    currency: str
    base_fee: Decimal
    per_kg_fee: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
