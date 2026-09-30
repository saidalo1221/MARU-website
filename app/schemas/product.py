from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.product import ALLOWED_VOLUMES_ML


class SKUOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_code: str
    barcode: Optional[str]
    retail_price: Decimal
    wholesale_price: Optional[Decimal]
    distributor_price: Optional[Decimal]
    export_price: Optional[Decimal]
    special_price: Optional[Decimal]
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
    color_hex: Optional[str]
    photo_url: Optional[str]
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
    shape: Optional[str]
    purpose: Optional[str]
    description: Optional[str]
    country_of_origin: Optional[str]
    min_order_quantity: int
    badge_mode: str
    badge_new: Optional[bool]
    badge_sale: Optional[bool]
    badge_bestseller: Optional[bool]
    variants: list[ProductVariantOut]
    badges: Optional[ProductBadges] = None


class SKUCreate(BaseModel):
    sku_code: str = Field(min_length=1, max_length=100)
    barcode: Optional[str] = Field(default=None, max_length=50)
    retail_price: Decimal = Field(gt=0)
    wholesale_price: Optional[Decimal] = Field(default=None, gt=0)
    distributor_price: Optional[Decimal] = Field(default=None, gt=0)
    export_price: Optional[Decimal] = Field(default=None, gt=0)
    special_price: Optional[Decimal] = Field(default=None, gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    unit_weight_g: Optional[int] = Field(default=None, ge=0)
    box_quantity: Optional[int] = Field(default=None, ge=0)
    box_weight_g: Optional[int] = Field(default=None, ge=0)
    box_length_mm: Optional[int] = Field(default=None, ge=0)
    box_width_mm: Optional[int] = Field(default=None, ge=0)
    box_height_mm: Optional[int] = Field(default=None, ge=0)
    is_active: bool = True


class SKUUpdate(BaseModel):
    barcode: Optional[str] = Field(default=None, max_length=50)
    retail_price: Optional[Decimal] = Field(default=None, gt=0)
    wholesale_price: Optional[Decimal] = Field(default=None, gt=0)
    distributor_price: Optional[Decimal] = Field(default=None, gt=0)
    export_price: Optional[Decimal] = Field(default=None, gt=0)
    special_price: Optional[Decimal] = Field(default=None, gt=0)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    unit_weight_g: Optional[int] = Field(default=None, ge=0)
    box_quantity: Optional[int] = Field(default=None, ge=0)
    box_weight_g: Optional[int] = Field(default=None, ge=0)
    box_length_mm: Optional[int] = Field(default=None, ge=0)
    box_width_mm: Optional[int] = Field(default=None, ge=0)
    box_height_mm: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class VariantImageCreate(BaseModel):
    image_url: str = Field(min_length=1, max_length=500)


class VariantImageReorder(BaseModel):
    sort_order: int


class ProductVariantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    color: str = Field(min_length=1, max_length=100)
    color_hex: Optional[str] = Field(default=None, max_length=7)
    photo_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = True


class ProductVariantUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    color: Optional[str] = Field(default=None, min_length=1, max_length=100)
    color_hex: Optional[str] = Field(default=None, max_length=7)
    photo_url: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class ProductCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    volume_ml: int
    shape: Optional[str] = Field(default=None, max_length=100)
    purpose: Optional[str] = Field(default=None, max_length=255)
    length_mm: Optional[int] = Field(default=None, ge=0)
    width_mm: Optional[int] = Field(default=None, ge=0)
    height_mm: Optional[int] = Field(default=None, ge=0)
    weight_g: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None
    country_of_origin: Optional[str] = Field(default=None, max_length=100)
    min_order_quantity: int = Field(default=1, ge=1)
    badge_mode: Literal["auto", "manual"] = "auto"
    badge_new: Optional[bool] = None
    badge_sale: Optional[bool] = None
    badge_bestseller: Optional[bool] = None

    @field_validator("volume_ml")
    @classmethod
    def _validate_volume(cls, v: int) -> int:
        if v not in ALLOWED_VOLUMES_ML:
            raise ValueError(f"volume_ml must be one of {ALLOWED_VOLUMES_ML}")
        return v


class ProductUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=255)
    volume_ml: Optional[int] = None
    shape: Optional[str] = Field(default=None, max_length=100)
    purpose: Optional[str] = Field(default=None, max_length=255)
    length_mm: Optional[int] = Field(default=None, ge=0)
    width_mm: Optional[int] = Field(default=None, ge=0)
    height_mm: Optional[int] = Field(default=None, ge=0)
    weight_g: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None
    country_of_origin: Optional[str] = Field(default=None, max_length=100)
    min_order_quantity: Optional[int] = Field(default=None, ge=1)
    badge_mode: Optional[Literal["auto", "manual"]] = None
    badge_new: Optional[bool] = None
    badge_sale: Optional[bool] = None
    badge_bestseller: Optional[bool] = None

    @field_validator("volume_ml")
    @classmethod
    def _validate_volume(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in ALLOWED_VOLUMES_ML:
            raise ValueError(f"volume_ml must be one of {ALLOWED_VOLUMES_ML}")
        return v


class ProductTranslationIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    shape: Optional[str] = Field(default=None, max_length=100)
    purpose: Optional[str] = Field(default=None, max_length=255)
    country_of_origin: Optional[str] = Field(default=None, max_length=100)


class ProductTranslationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    locale: str
    name: str
    description: Optional[str]
    shape: Optional[str]
    purpose: Optional[str]
    country_of_origin: Optional[str]
