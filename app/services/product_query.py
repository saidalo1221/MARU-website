"""Finding the products of one catalogue page in SQL (PRD ТЗ№1 §46: the catalogue must stay fast with 100 000+
products). Filtering, price filtering, sorting and paging all happen in the database and only the ids of the
requested page come back; the page's products are then loaded in full. Nothing here loads the whole catalogue.

The price of a product is that of its cheapest active SKU, using the sale price (`special_price` below retail)
when there is one - the same rule the storefront shows on the card. With a target currency the prices are
converted through USD with the stored exchange rates; without one they are compared as stored.
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.models import Inventory, Order, OrderItem, Product, ProductVariant, SKU, Warehouse
from app.models.exchange_rate import ExchangeRate
from app.models.review import Review, ReviewStatus
from app.services.badges import _SOLD_STATUSES
from app.services.currency import get_rate_to_usd
from app.services import product_search
from app.models import Category
from app.models.product_translation import ProductTranslation


def _effective_price():
    return case((and_(SKU.special_price.is_not(None), SKU.special_price < SKU.retail_price), SKU.special_price), else_=SKU.retail_price)


def find_product_ids(
    db: Session,
    conditions: list,
    availability_in_stock: bool,
    price_min: Optional[Decimal],
    price_max: Optional[Decimal],
    currency: Optional[str],
    sort: Optional[str],
    page: int,
    limit: Optional[int],
    text: Optional[str] = None,
    lang: Optional[str] = None,
) -> tuple:
    """Returns (ids of the requested page in display order, total number of matching products).
    `text` adds a search over names / SKU codes / categories / volume (ranked by relevance unless a sort is
    given); if it finds nothing, a typo-tolerant pass is used instead. May raise CurrencyError when `currency`
    has no exchange rate."""
    words = product_search.tokens(text) if text else []
    if text and not words:
        return [], 0
    if words:
        ids, total = _run(db, conditions, availability_in_stock, price_min, price_max, currency, sort, page, limit, words, lang)
        if total == 0:
            near = product_search.fuzzy_product_ids(db, words, lang, conditions)
            if near:
                ids, total = _run(db, conditions + [Product.id.in_(near)], availability_in_stock, price_min, price_max, currency, sort, page, limit, None, None)
        return ids, total
    return _run(db, conditions, availability_in_stock, price_min, price_max, currency, sort, page, limit, None, None)


def _run(db, conditions, availability_in_stock, price_min, price_max, currency, sort, page, limit, words, lang) -> tuple:
    effective = _effective_price()
    convert = currency is not None and (price_min is not None or price_max is not None or sort in ("price_asc", "price_desc"))
    if convert:
        target_rate = get_rate_to_usd(db, currency)
        price = effective / func.coalesce(ExchangeRate.units_per_usd, 1) * target_rate
    else:
        price = effective
    min_price = func.min(price)

    stmt = (
        select(Product.id.label("pid"), min_price.label("minp"))
        .select_from(Product)
        .join(ProductVariant, ProductVariant.product_id == Product.id)
        .join(SKU, SKU.variant_id == ProductVariant.id)
        .where(*conditions, *(product_search.text_filter(words, lang) if words else []))
        .group_by(Product.id)
    )
    if words:
        stmt = stmt.join(Category, Category.id == Product.category_id)
        if lang:
            stmt = stmt.outerjoin(ProductTranslation, and_(ProductTranslation.product_id == Product.id, ProductTranslation.locale == lang))
    if convert:
        stmt = stmt.outerjoin(ExchangeRate, ExchangeRate.currency == SKU.currency)

    if availability_in_stock:
        in_stock = (
            select(Inventory.sku_id)
            .join(Warehouse, Warehouse.id == Inventory.warehouse_id)
            .where(Warehouse.is_active.is_(True))
            .group_by(Inventory.sku_id)
            .having(func.sum(Inventory.stock - Inventory.reserved) > 0)
        )
        stmt = stmt.having(func.sum(case((SKU.id.in_(in_stock), 1), else_=0)) > 0)
    if price_min is not None:
        stmt = stmt.having(min_price >= price_min)
    if price_max is not None:
        stmt = stmt.having(min_price <= price_max)

    if sort == "popularity":
        sold = (
            select(ProductVariant.product_id.label("pid"), func.sum(OrderItem.quantity).label("sold"))
            .select_from(OrderItem)
            .join(SKU, SKU.id == OrderItem.sku_id)
            .join(ProductVariant, ProductVariant.id == SKU.variant_id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.status.in_(_SOLD_STATUSES))
            .group_by(ProductVariant.product_id)
            .subquery()
        )
        stmt = stmt.outerjoin(sold, sold.c.pid == Product.id)
        order_by = [func.coalesce(func.max(sold.c.sold), 0).desc(), Product.id]
    elif sort == "rating":
        rated = (
            select(Review.product_id.label("pid"), func.avg(Review.rating).label("avg"), func.count(Review.id).label("n"))
            .where(Review.status == ReviewStatus.APPROVED)
            .group_by(Review.product_id)
            .subquery()
        )
        stmt = stmt.outerjoin(rated, rated.c.pid == Product.id)
        order_by = [func.coalesce(func.max(rated.c.avg), 0).desc(), func.coalesce(func.max(rated.c.n), 0).desc(), Product.id]
    elif sort == "price_asc":
        order_by = [min_price.asc(), Product.id]
    elif sort == "price_desc":
        order_by = [min_price.desc(), Product.id]
    elif sort == "newest":
        order_by = [Product.id.desc()]
    elif words:
        order_by = [product_search.relevance(words), Product.id]
    else:
        order_by = [Product.id]

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    paged = stmt.order_by(*order_by)
    if limit is not None:
        paged = paged.limit(limit).offset((page - 1) * limit)
    ids = [row.pid for row in db.execute(paged)]
    return ids, total
