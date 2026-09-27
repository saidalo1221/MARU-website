from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.promo_code import PromoDiscountType


class PromoCodeCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    discount_type: PromoDiscountType
    discount_value: Decimal = Field(gt=0)
    currency: str | None = None
    min_order_amount: Decimal = Decimal("0")
    max_uses: int | None = Field(default=None, ge=1)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool = True


class PromoCodeUpdate(BaseModel):
    discount_type: PromoDiscountType | None = None
    discount_value: Decimal | None = Field(default=None, gt=0)
    currency: str | None = None
    min_order_amount: Decimal | None = None
    max_uses: int | None = Field(default=None, ge=1)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool | None = None


class PromoCodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    discount_type: PromoDiscountType
    discount_value: Decimal
    currency: str | None
    min_order_amount: Decimal
    max_uses: int | None
    used_count: int
    valid_from: datetime | None
    valid_until: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
