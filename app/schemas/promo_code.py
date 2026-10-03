from typing import Optional
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.promo_code import PromoDiscountType


class PromoCodeCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    discount_type: PromoDiscountType
    discount_value: Decimal = Field(gt=0)
    currency: Optional[str] = None
    min_order_amount: Decimal = Decimal("0")
    max_uses: Optional[int] = Field(default=None, ge=1)
    max_uses_per_customer: Optional[int] = Field(default=None, ge=1)
    product_ids: Optional[list[int]] = None
    category_ids: Optional[list[int]] = None
    countries: Optional[list[str]] = None
    customer_ids: Optional[list[int]] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True


class PromoCodeUpdate(BaseModel):
    discount_type: Optional[PromoDiscountType] = None
    discount_value: Optional[Decimal] = Field(default=None, gt=0)
    currency: Optional[str] = None
    min_order_amount: Optional[Decimal] = None
    max_uses: Optional[int] = Field(default=None, ge=1)
    max_uses_per_customer: Optional[int] = Field(default=None, ge=1)
    product_ids: Optional[list[int]] = None
    category_ids: Optional[list[int]] = None
    countries: Optional[list[str]] = None
    customer_ids: Optional[list[int]] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None


class PromoCodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    discount_type: PromoDiscountType
    discount_value: Decimal
    currency: Optional[str]
    min_order_amount: Decimal
    max_uses: Optional[int]
    used_count: int
    max_uses_per_customer: Optional[int] = None
    product_ids: Optional[list[int]] = None
    category_ids: Optional[list[int]] = None
    countries: Optional[list[str]] = None
    customer_ids: Optional[list[int]] = None
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
