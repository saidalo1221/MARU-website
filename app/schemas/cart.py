from decimal import Decimal

from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    sku_id: int
    quantity: int = Field(gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CartCurrencyUpdate(BaseModel):
    currency: str = Field(min_length=3, max_length=3)


class CartItemOut(BaseModel):
    id: int
    sku_id: int
    sku_code: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class CartOut(BaseModel):
    id: int
    currency: str
    items: list[CartItemOut]
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    delivery: Decimal
    total: Decimal
    item_count: int
    promo_code: str | None = None
