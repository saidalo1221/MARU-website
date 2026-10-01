from typing import Literal, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, contains_eager

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.models import Inventory, Product, ProductVariant, SKU
from app.models.product_translation import ProductTranslation
from app.schemas.product import ProductOut
from app.services.badges import compute_badges, compute_badges_batch
from app.services.catalog import MAX_PAGE_SIZE, SORT_OPTIONS, rating_stats, sales_counts
from app.services.currency import CurrencyError, convert_amount
from app.services.i18n import get_product_translation, get_product_translations

router = APIRouter(prefix="/products", tags=["products"])

_SKU_PRICE_FIELDS = ("retail_price", "wholesale_price", "distributor_price", "export_price", "special_price")


def _apply_translation(product: Product, translation: Optional[ProductTranslation]) -> ProductOut:
    out = ProductOut.model_validate(product)
    if translation is not None:
        out.name = translation.name
        if translation.description is not None:
            out.description = translation.description
        if translation.shape is not None:
            out.shape = translation.shape
        if translation.purpose is not None:
            out.purpose = translation.purpose
        if translation.country_of_origin is not None:
            out.country_of_origin = translation.country_of_origin
    return out


def _display_price(product: ProductOut) -> Decimal:
    """The "from" price shown on a card: the cheapest active SKU, sale price
    when there is one."""
    prices = [
        sku.special_price if sku.special_price is not None and sku.special_price < sku.retail_price else sku.retail_price
        for variant in product.variants
        for sku in variant.skus
        if sku.is_active
    ]
    return min(prices) if prices else Decimal("0")


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
                value: Optional[Decimal] = getattr(sku, field)
                if value is not None:
                    setattr(sku, field, convert_amount(db, value, sku.currency, currency))
            for tier in sku.quantity_tiers:
                tier.price = convert_amount(db, tier.price, sku.currency, currency)
            sku.currency = currency


@router.get("/", response_model=list[ProductOut], dependencies=[Depends(rate_limit("products_list", 120, 60))])
def list_active_products(
    response: Response,
    lang: Optional[str] = None,
    currency: Optional[str] = None,
    category_id: Optional[int] = None,
    capacity: Optional[int] = None,
    color: Optional[str] = None,
    material: Optional[str] = None,
    availability: Optional[Literal["in_stock"]] = None,
    price_min: Optional[Decimal] = Query(default=None, ge=0),
    price_max: Optional[Decimal] = Query(default=None, ge=0),
    sort: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: Optional[int] = Query(default=None, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
) -> list[ProductOut]:
    """Fetch plastic containers that currently have at least one active
    variant with at least one active, sellable SKU (PRD section 61 MVP catalog).
    Pass ?lang=ru|uz|en for translated name/description (PRD section 15).
    Pass ?currency=UZS|EUR|KZT|AED to display prices converted from each
    SKU's stored currency (PRD section 14), same as the cart.

    Optional filters (PRD ТЗ№3 §44/§52): category_id, capacity (ml), color,
    material, availability=in_stock, price_min/price_max (in the requested
    currency). ?sort= is one of price_asc, price_desc, newest, popularity,
    rating (whitelist, §53). Without ?limit the whole list is returned as
    before; with it, results are paged (?page, limit <= 100). Either way the
    X-Total-Count header carries the number of matches before paging."""
    if sort is not None and sort not in SORT_OPTIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"sort must be one of {', '.join(SORT_OPTIONS)}")

    conditions = [ProductVariant.is_active.is_(True), SKU.is_active.is_(True)]
    if category_id is not None:
        conditions.append(Product.category_id == category_id)
    if capacity is not None:
        conditions.append(Product.volume_ml == capacity)
    if material:
        conditions.append(Product.material == material)
    if color:
        conditions.append(func.lower(ProductVariant.color) == color.strip().lower())

    stmt = (
        select(Product)
        .join(Product.variants)
        .join(ProductVariant.skus)
        .where(*conditions)
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

    if availability == "in_stock":
        products = [
            p for p in products
            if any(s.is_active and s.available_quantity > 0 for v in p.variants for s in v.skus)
        ]

    translations = get_product_translations(db, [p.id for p in products], lang) if lang else {}
    badges = compute_badges_batch(db, products)
    ratings = rating_stats(db, [p.id for p in products])
    out = [_apply_translation(p, translations.get(p.id)) for p in products]
    for product, product_out in zip(products, out):
        product_out.badges = badges[product.id]
        if product.id in ratings:
            product_out.rating_average, product_out.rating_count = ratings[product.id]

    if currency:
        try:
            for product in out:
                _convert_product_prices(db, product, currency)
        except CurrencyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if price_min is not None or price_max is not None:
        out = [
            p for p in out
            if (price_min is None or _display_price(p) >= price_min) and (price_max is None or _display_price(p) <= price_max)
        ]

    if sort == "price_asc":
        out.sort(key=_display_price)
    elif sort == "price_desc":
        out.sort(key=_display_price, reverse=True)
    elif sort == "newest":
        out.sort(key=lambda p: p.id, reverse=True)
    elif sort == "rating":
        out.sort(key=lambda p: (p.rating_average or 0, p.rating_count), reverse=True)
    elif sort == "popularity":
        sold = sales_counts(db, [p.id for p in out])
        out.sort(key=lambda p: sold.get(p.id, 0), reverse=True)

    response.headers["X-Total-Count"] = str(len(out))
    if limit is not None:
        out = out[(page - 1) * limit : page * limit]
    return out


@router.get("/{slug}", response_model=ProductOut, dependencies=[Depends(rate_limit("products_detail", 120, 60))])
def get_active_product(
    slug: str, lang: Optional[str] = None, currency: Optional[str] = None, db: Session = Depends(get_db)
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
    out.badges = compute_badges(db, product)
    stats = rating_stats(db, [product.id]).get(product.id)
    if stats is not None:
        out.rating_average, out.rating_count = stats

    if currency:
        try:
            _convert_product_prices(db, out, currency)
        except CurrencyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return out
