from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, contains_eager

from app.database import get_db
from app.models import Inventory, Product, ProductVariant, SKU
from app.models.product_translation import ProductTranslation
from app.schemas.product import ProductOut
from app.services.currency import CurrencyError, convert_amount
from app.services.i18n import get_product_translation, get_product_translations

router = APIRouter(prefix="/products", tags=["products"])

_SKU_PRICE_FIELDS = ("retail_price", "wholesale_price", "distributor_price", "export_price", "special_price")


def _apply_translation(product: Product, translation: ProductTranslation | None) -> ProductOut:
    out = ProductOut.model_validate(product)
    if translation is not None:
        out.name = translation.name
        if translation.description is not None:
            out.description = translation.description
    return out


def _convert_product_prices(db: Session, product: ProductOut, currency: str) -> None:
    """Converts every SKU's price fields (on the already-detached Pydantic
    copy, never the ORM row) from that SKU's own stored currency into
    `currency`, so the catalog reflects the same display currency the cart
    uses (PRD section 14). Raises CurrencyError if no rate is configured."""
    for variant in product.variants:
        for sku in variant.skus:
            if sku.currency == currency:
                continue
            for field in _SKU_PRICE_FIELDS:
                value: Decimal | None = getattr(sku, field)
                if value is not None:
                    setattr(sku, field, convert_amount(db, value, sku.currency, currency))
            sku.currency = currency


@router.get("/", response_model=list[ProductOut])
def list_active_products(
    lang: str | None = None, currency: str | None = None, db: Session = Depends(get_db)
) -> list[ProductOut]:
    """Fetch plastic containers that currently have at least one active
    variant with at least one active, sellable SKU (PRD section 61 MVP catalog).
    Pass ?lang=ru|uz|en for translated name/description (PRD section 15).
    Pass ?currency=UZS|EUR|KZT|AED to display prices converted from each
    SKU's stored currency (PRD section 14), same as the cart."""
    stmt = (
        select(Product)
        .join(Product.variants)
        .join(ProductVariant.skus)
        .where(ProductVariant.is_active.is_(True), SKU.is_active.is_(True))
        .options(
            contains_eager(Product.variants)
            .contains_eager(ProductVariant.skus)
            .joinedload(SKU.inventories).joinedload(Inventory.warehouse)
        )
        .order_by(Product.id)
    )

    try:
        products = db.execute(stmt).unique().scalars().all()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch products") from exc

    translations = get_product_translations(db, [p.id for p in products], lang) if lang else {}
    out = [_apply_translation(p, translations.get(p.id)) for p in products]

    if currency:
        try:
            for product in out:
                _convert_product_prices(db, product, currency)
        except CurrencyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return out


@router.get("/{slug}", response_model=ProductOut)
def get_active_product(
    slug: str, lang: str | None = None, currency: str | None = None, db: Session = Depends(get_db)
) -> ProductOut:
    """Fetch a single active product by slug for the product card view (PRD section 30).
    Pass ?currency=UZS|EUR|KZT|AED to display prices converted from the SKU's
    stored currency (PRD section 14), same as the cart."""
    stmt = (
        select(Product)
        .join(Product.variants)
        .join(ProductVariant.skus)
        .where(Product.slug == slug, ProductVariant.is_active.is_(True), SKU.is_active.is_(True))
        .options(
            contains_eager(Product.variants)
            .contains_eager(ProductVariant.skus)
            .joinedload(SKU.inventories).joinedload(Inventory.warehouse)
        )
    )

    try:
        product = db.execute(stmt).unique().scalar_one_or_none()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch product") from exc

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    translation = get_product_translation(db, product.id, lang) if lang else None
    out = _apply_translation(product, translation)

    if currency:
        try:
            _convert_product_prices(db, out, currency)
        except CurrencyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return out
