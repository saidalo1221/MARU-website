from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.product import ALLOWED_VOLUMES_ML


class SKUOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_code: str
    barcode: str | None
    retail_price: Decimal
    wholesale_price: Decimal | None
    distributor_price: Decimal | None
    export_price: Decimal | None
    special_price: Decimal | None
    currency: str
    is_active: bool
    available_quantity: int


class VariantImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    variant_id: int
    image_url: str
    sort_order: int


class ProductVariantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
    color_hex: str | None
    photo_url: str | None
    is_active: bool
    skus: list[SKUOut]
    images: list[VariantImageOut] = []


class ProductBadges(BaseModel):
    is_new: bool
    is_sale: bool
    is_bestseller: bool
    is_out_of_stock: bool


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    name: str
    slug: str
    volume_ml: int
    material: str
    shape: str | None
    purpose: str | None
    description: str | None
    country_of_origin: str | None
    min_order_quantity: int
    badge_mode: str
    badge_new: bool | None
    badge_sale: bool | None
    badge_bestseller: bool | None
    variants: list[ProductVariantOut]
    badges: ProductBadges | None = None


class SKUCreate(BaseModel):
    sku_code: str = Field(min_length=1, max_length=100)
    barcode: str | None = Field(default=None, max_length=50)
    retail_price: Decimal = Field(gt=0)
    wholesale_price: Decimal | None = Field(default=None, gt=0)
    distributor_price: Decimal | None = Field(default=None, gt=0)
    export_price: Decimal | None = Field(default=None, gt=0)
    special_price: Decimal | None = Field(default=None, gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    unit_weight_g: int | None = Field(default=None, ge=0)
    box_quantity: int | None = Field(default=None, ge=0)
    box_weight_g: int | None = Field(default=None, ge=0)
    box_length_mm: int | None = Field(default=None, ge=0)
    box_width_mm: int | None = Field(default=None, ge=0)
    box_height_mm: int | None = Field(default=None, ge=0)
    is_active: bool = True


class SKUUpdate(BaseModel):
    barcode: str | None = Field(default=None, max_length=50)
    retail_price: Decimal | None = Field(default=None, gt=0)
    wholesale_price: Decimal | None = Field(default=None, gt=0)
    distributor_price: Decimal | None = Field(default=None, gt=0)
    export_price: Decimal | None = Field(default=None, gt=0)
    special_price: Decimal | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    unit_weight_g: int | None = Field(default=None, ge=0)
    box_quantity: int | None = Field(default=None, ge=0)
    box_weight_g: int | None = Field(default=None, ge=0)
    box_length_mm: int | None = Field(default=None, ge=0)
    box_width_mm: int | None = Field(default=None, ge=0)
    box_height_mm: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class VariantImageCreate(BaseModel):
    image_url: str = Field(min_length=1, max_length=500)


class VariantImageReorder(BaseModel):
    sort_order: int


class ProductVariantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    color: str = Field(min_length=1, max_length=100)
    color_hex: str | None = Field(default=None, max_length=7)
    photo_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class ProductVariantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    color: str | None = Field(default=None, min_length=1, max_length=100)
    color_hex: str | None = Field(default=None, max_length=7)
    photo_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ProductCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    volume_ml: int
    shape: str | None = Field(default=None, max_length=100)
    purpose: str | None = Field(default=None, max_length=255)
    length_mm: int | None = Field(default=None, ge=0)
    width_mm: int | None = Field(default=None, ge=0)
    height_mm: int | None = Field(default=None, ge=0)
    weight_g: int | None = Field(default=None, ge=0)
    description: str | None = None
    country_of_origin: str | None = Field(default=None, max_length=100)
    min_order_quantity: int = Field(default=1, ge=1)
    badge_mode: Literal["auto", "manual"] = "auto"
    badge_new: bool | None = None
    badge_sale: bool | None = None
    badge_bestseller: bool | None = None

    @field_validator("volume_ml")
    @classmethod
    def _validate_volume(cls, v: int) -> int:
        if v not in ALLOWED_VOLUMES_ML:
            raise ValueError(f"volume_ml must be one of {ALLOWED_VOLUMES_ML}")
        return v


class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    volume_ml: int | None = None
    shape: str | None = Field(default=None, max_length=100)
    purpose: str | None = Field(default=None, max_length=255)
    length_mm: int | None = Field(default=None, ge=0)
    width_mm: int | None = Field(default=None, ge=0)
    height_mm: int | None = Field(default=None, ge=0)
    weight_g: int | None = Field(default=None, ge=0)
    description: str | None = None
    country_of_origin: str | None = Field(default=None, max_length=100)
    min_order_quantity: int | None = Field(default=None, ge=1)
    badge_mode: Literal["auto", "manual"] | None = None
    badge_new: bool | None = None
    badge_sale: bool | None = None
    badge_bestseller: bool | None = None

    @field_validator("volume_ml")
    @classmethod
    def _validate_volume(cls, v: int | None) -> int | None:
        if v is not None and v not in ALLOWED_VOLUMES_ML:
            raise ValueError(f"volume_ml must be one of {ALLOWED_VOLUMES_ML}")
        return v


class ProductTranslationIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    shape: str | None = Field(default=None, max_length=100)
    purpose: str | None = Field(default=None, max_length=255)
    country_of_origin: str | None = Field(default=None, max_length=100)


class ProductTranslationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    locale: str
    name: str
    description: str | None
    shape: str | None
    purpose: str | None
    country_of_origin: str | None
