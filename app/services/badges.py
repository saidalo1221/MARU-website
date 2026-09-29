"""Computes product badges (New / Sale / Best Seller / Out of Stock).

Each product has a `badge_mode` of "auto" or "manual" (admin-controlled,
PRD product-badges feature). In "auto" mode, New/Sale/Best Seller are
derived from data already on the loaded Product/variants/SKUs plus one
batched sales-volume query. In "manual" mode the admin's own
badge_new/badge_sale/badge_bestseller flags are used instead. Out of Stock
is always computed live in both modes — it's a factual availability state,
not a marketing choice.
"""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Order, OrderItem, Product, ProductVariant, SKU
from app.models.enums import OrderStatus
from app.schemas.product import ProductBadges

# A product counts as "New" for this many days after creation.
NEW_DAYS_THRESHOLD = 14

# Total units sold (across paid-or-later orders) to count as "Best Seller".
BESTSELLER_MIN_SOLD = 20

# Order states that represent a real, committed sale — excludes carts that
# never paid (new/payment_pending), failed payments, and cancellations.
_SOLD_STATUSES = (
    OrderStatus.PAID,
    OrderStatus.PROCESSING,
    OrderStatus.PACKED,
    OrderStatus.SHIPPED,
    OrderStatus.IN_TRANSIT,
    OrderStatus.DELIVERED,
    OrderStatus.PARTIALLY_REFUNDED,
)


def _is_out_of_stock(product: Product) -> bool:
    return not any(
        sku.is_active and sku.available_quantity > 0
        for variant in product.variants
        for sku in variant.skus
    )


def _is_on_sale(product: Product) -> bool:
    return any(
        sku.is_active and sku.special_price is not None and sku.special_price < sku.retail_price
        for variant in product.variants
        for sku in variant.skus
    )


def _is_new(product: Product) -> bool:
    if product.created_at is None:
        return False
    return datetime.utcnow() - product.created_at <= timedelta(days=NEW_DAYS_THRESHOLD)


def _bestseller_product_ids(db: Session, product_ids: list[int]) -> set[int]:
    """Batched: which of these products have sold >= BESTSELLER_MIN_SOLD
    total units across all their SKUs, in one grouped query."""
    if not product_ids:
        return set()

    stmt = (
        select(Product.id, func.coalesce(func.sum(OrderItem.quantity), 0))
        .select_from(Product)
        .join(ProductVariant, ProductVariant.product_id == Product.id)
        .join(SKU, SKU.variant_id == ProductVariant.id)
        .join(OrderItem, OrderItem.sku_id == SKU.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Product.id.in_(product_ids), Order.status.in_(_SOLD_STATUSES))
        .group_by(Product.id)
        .having(func.coalesce(func.sum(OrderItem.quantity), 0) >= BESTSELLER_MIN_SOLD)
    )
    return {row[0] for row in db.execute(stmt)}


def compute_badges_batch(db: Session, products: list[Product]) -> dict[int, ProductBadges]:
    """One badges computation per product, sharing a single bestseller query
    across the whole batch (used by list endpoints)."""
    bestseller_ids = _bestseller_product_ids(db, [p.id for p in products])
    result: dict[int, ProductBadges] = {}
    for product in products:
        if product.badge_mode == "manual":
            is_new = bool(product.badge_new)
            is_sale = bool(product.badge_sale)
            is_bestseller = bool(product.badge_bestseller)
        else:
            is_new = _is_new(product)
            is_sale = _is_on_sale(product)
            is_bestseller = product.id in bestseller_ids
        result[product.id] = ProductBadges(
            is_new=is_new,
            is_sale=is_sale,
            is_bestseller=is_bestseller,
            is_out_of_stock=_is_out_of_stock(product),
        )
    return result


def compute_badges(db: Session, product: Product) -> ProductBadges:
    return compute_badges_batch(db, [product])[product.id]
