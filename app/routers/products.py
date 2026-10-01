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
from app.services.catalog import MAX_PAGE_SIZE, SORT_OPTIONS, rating_stats
from app.services.product_query import find_product_ids
from app.services.product_search import search_ids
from app.core import cache
from app.config import settings
from app.models import Category
from app.schemas.product import CategorySuggestionOut, FacetsOut, ProductSuggestionOut, SuggestOut
from app.services.product_search import tokens
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
        for field in ("seo_title", "meta_description", "advantages", "usage_scenarios", "instructions", "material_info"):
            value = getattr(translation, field)
            if value:
                setattr(out, field, value)
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


def _present(db: Session, ids: list, conditions: list, lang: Optional[str], currency: Optional[str]) -> list:
    """Loads the products with these ids (only their active variants/SKUs matching `conditions`), in the given order,
    and turns them into API objects: translated, with badges, ratings and converted prices."""
    if not ids:
        return []
    stmt = (
        select(Product)
        .join(Product.variants)
        .join(ProductVariant.skus)
        .where(Product.id.in_(ids), *conditions)
        .options(
            contains_eager(Product.variants)
            .contains_eager(ProductVariant.skus)
            .joinedload(SKU.inventories).joinedload(Inventory.warehouse)
        )
    )
    try:
        loaded = {p.id: p for p in db.execute(stmt).unique().scalars().all()}
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch products") from exc
    products = [loaded[i] for i in ids if i in loaded]  # keep the order the database chose

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

    return out


@router.get("/", response_model=list[ProductOut], dependencies=[Depends(rate_limit("products_list", 120, 60))])
def list_active_products(
    response: Response,
    lang: Optional[str] = None,
    currency: Optional[str] = None,
    q: Optional[str] = Query(default=None, max_length=80, description="Search words: name, SKU code, category, shape/purpose or volume; typo tolerant"),
    category_id: Optional[int] = None,
    category_ids: Optional[str] = Query(default=None, description="Comma-separated category ids (a category and its children)", max_length=200),
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
    rating (whitelist, §53). Results are paged (?page, ?limit, at most 100; 100 when
    no limit is given). Either way the
    X-Total-Count header carries the number of matches before paging."""
    if sort is not None and sort not in SORT_OPTIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"sort must be one of {', '.join(SORT_OPTIONS)}")

    conditions = [ProductVariant.is_active.is_(True), SKU.is_active.is_(True)]
    if category_id is not None:
        conditions.append(Product.category_id == category_id)
    if category_ids:
        try:
            conditions.append(Product.category_id.in_([int(x) for x in category_ids.split(",") if x.strip()]))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="category_ids must be comma-separated numbers") from exc
    if capacity is not None:
        conditions.append(Product.volume_ml == capacity)
    if material:
        conditions.append(Product.material == material)
    if color:
        conditions.append(func.lower(ProductVariant.color) == color.strip().lower())

    # The database filters, sorts and pages (app/services/product_query.py); only this page's products are loaded.
    limit = limit or MAX_PAGE_SIZE  # never an unbounded list: a catalogue can hold 100 000+ products
    try:
        ids, total = find_product_ids(
            db, conditions, availability == "in_stock", price_min, price_max, currency, sort, page, limit, text=q, lang=lang
        )
    except CurrencyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch products") from exc

    response.headers["X-Total-Count"] = str(total)
    return _present(db, ids, conditions, lang, currency)


def _sellable_conditions() -> list:
    return [ProductVariant.is_active.is_(True), SKU.is_active.is_(True)]


@router.get("/suggest", response_model=SuggestOut, dependencies=[Depends(rate_limit("products_suggest", 240, 60))])
def suggest(
    q: str = Query(min_length=1, max_length=80),
    lang: Optional[str] = None,
    limit: int = Query(default=6, ge=1, le=12),
    db: Session = Depends(get_db),
) -> SuggestOut:
    """Autocomplete: the best few products and matching categories for what has been typed so far."""
    conditions = _sellable_conditions()
    try:
        ids, _total = search_ids(db, q, lang, conditions, 1, limit)
        rows = db.execute(select(Product).where(Product.id.in_(ids))).scalars().all() if ids else []
        by_id = {p.id: p for p in rows}
        translations = get_product_translations(db, ids, lang) if lang and ids else {}
        words = tokens(q)
        cats = []
        if words:
            cats = db.execute(
                select(Category).where(*[func.lower(Category.name).like(f"%{w}%") for w in words]).order_by(Category.id).limit(3)
            ).scalars().all()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Search failed") from exc
    products = [
        ProductSuggestionOut(
            id=i, name=(translations[i].name if i in translations else by_id[i].name), slug=by_id[i].slug,
            volume_ml=by_id[i].volume_ml, category_id=by_id[i].category_id,
        )
        for i in ids if i in by_id
    ]
    return SuggestOut(products=products, categories=[CategorySuggestionOut(id=c.id, name=c.name, slug=c.slug) for c in cats])


@router.get("/facets", response_model=FacetsOut, dependencies=[Depends(rate_limit("products_facets", 120, 60))])
def facets(category_ids: Optional[str] = Query(default=None, max_length=200), db: Session = Depends(get_db)) -> dict:
    """The filter choices that exist in the catalogue (volumes, colours, materials, categories), cached."""
    ids = None
    if category_ids:
        try:
            ids = sorted(int(x) for x in category_ids.split(",") if x.strip())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="category_ids must be comma-separated numbers") from exc

    def load() -> dict:
        conditions = _sellable_conditions()
        if ids:
            conditions.append(Product.category_id.in_(ids))
        base = select(Product.volume_ml, Product.material, Product.category_id, ProductVariant.color).join(
            ProductVariant, ProductVariant.product_id == Product.id
        ).join(SKU, SKU.variant_id == ProductVariant.id).where(*conditions).distinct()
        rows = db.execute(base).all()
        return {
            "capacities": sorted({r.volume_ml for r in rows}),
            "colors": sorted({r.color for r in rows if r.color}),
            "materials": sorted({r.material for r in rows if r.material}),
            "category_ids": sorted({r.category_id for r in rows}),
        }

    return cache.get_or_set("catalog", f"facets:{ids or ''}", settings.CACHE_TTL_SECONDS, load)


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
