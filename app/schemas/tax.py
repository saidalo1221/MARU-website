from typing import Optional
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TaxRuleCreate(BaseModel):
    country: str = Field(min_length=1, max_length=100, description="Country name, or '*' for any country")
    region: str = Field(default="*", min_length=1, max_length=100, description="State/province, or '*' for any")
    customer_type: str = Field(min_length=1, max_length=20, description="A CustomerType value, or '*' for any")
    tax_type: str = Field(default="vat", min_length=1, max_length=30)
    rate: Decimal = Field(default=Decimal("0"), ge=0, le=100, description="Percentage, e.g. 12.00 for 12%")
    min_order_amount: Decimal = Field(default=Decimal("0"), ge=0, description="Applies from this taxable amount, in USD")
    is_active: bool = True


class TaxRuleUpdate(BaseModel):
    rate: Optional[Decimal] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None


class TaxRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country: str
    region: str
    customer_type: str
    tax_type: str
    rate: Decimal
    min_order_amount: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
