from typing import Optional
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.product import ProductOut


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
    min_order_quantity: int = 1
    unit_price: Decimal
    line_total: Decimal
    # What the line shows: product, variant, picture and, when the customer's
    # price is below the list (retail) price, that old price (PRD ТЗ№2 §20).
    product_name: Optional[str] = None
    product_slug: Optional[str] = None
    variant_name: Optional[str] = None
    image_url: Optional[str] = None
    list_price: Optional[Decimal] = None
    # False when the product is not sold in the visitor's market (?market_country=).
    available_in_market: bool = True


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
    promo_code: Optional[str] = None
    # Not part of any total; shown in a separate "Saved for later" list.
    saved_items: list[CartItemOut] = []
    # Cart currency. Remaining is 0 once shipping is free; both None = no offer.
    free_shipping_threshold: Optional[Decimal] = None
    free_shipping_remaining: Optional[Decimal] = None
    # Boxes / weight / volume of the cart (app/services/packaging.py); None for an empty cart.
    packaging: Optional[dict] = None
    # Loyalty points: what the signed-in retail customer can spend, what is applied now (already inside `discount`).
    loyalty: Optional[dict] = None
    unavailable_items: int = 0
    loyalty_points_applied: int = 0
    loyalty_discount: Decimal = Decimal("0")


class CartRecommendationsOut(BaseModel):
    # True when at least one product was picked from real past-order
    # co-purchase data (drives "Frequently bought together" vs the softer
    # "You may also like" heading for best-seller/newest fill-ins).
    based_on_orders: bool
    products: list[ProductOut]
