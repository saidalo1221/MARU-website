"""Cart upsell ("Frequently bought together", PRD section 21).

Ranks other products for a cart in three tiers, each only filling slots the
previous tier left open: (1) products that appear in the same past orders as
the cart's products, (2) overall best sellers, (3) newest products. Needs no
extra table — co-purchase is derived from OrderItem rows.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Order, OrderItem, Product, ProductVariant, SKU
from app.services.badges import _SOLD_STATUSES

# Candidates are over-fetched because out-of-stock products are dropped in
# Python (stock is aggregated across warehouses, see SKU.available_quantity).
_OVERFETCH = 3


def _sellable_product_ids():
    """Products with at least one active variant that has an active SKU."""
    return (
        select(ProductVariant.product_id)
        .join(SKU, SKU.variant_id == ProductVariant.id)
        .where(ProductVariant.is_active.is_(True), SKU.is_active.is_(True))
    )


def recommended_product_ids(
    db: Session, cart_product_ids: set[int], limit: int
) -> tuple[list[int], int]:
    """Returns (ordered candidate product ids, how many leading ids came from
    real co-purchase history). Excludes products already in the cart."""
    fetch = limit * _OVERFETCH
    ids: list[int] = []

    def add(rows) -> None:
        for pid in rows:
            if pid not in ids and pid not in cart_product_ids:
                ids.append(pid)

    sold_units = func.coalesce(func.sum(OrderItem.quantity), 0)
    sold_base = (
        select(Product.id)
        .select_from(OrderItem)
        .join(SKU, SKU.id == OrderItem.sku_id)
        .join(ProductVariant, ProductVariant.id == SKU.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.status.in_(_SOLD_STATUSES), Product.id.in_(_sellable_product_ids()))
    )

    co_count = 0
    if cart_product_ids:
        orders_with_cart = (
            select(OrderItem.order_id)
            .join(SKU, SKU.id == OrderItem.sku_id)
            .join(ProductVariant, ProductVariant.id == SKU.variant_id)
            .where(ProductVariant.product_id.in_(cart_product_ids))
        )
        co_rows = db.execute(
            sold_base.where(Order.id.in_(orders_with_cart), Product.id.notin_(cart_product_ids))
            .group_by(Product.id)
            .order_by(sold_units.desc())
            .limit(fetch)
        ).scalars()
        add(co_rows)
        co_count = len(ids)

    if len(ids) < fetch:
        add(db.execute(sold_base.group_by(Product.id).order_by(sold_units.desc()).limit(fetch)).scalars())

    if len(ids) < fetch:
        newest = (
            select(Product.id)
            .where(Product.id.in_(_sellable_product_ids()))
            .order_by(Product.created_at.desc(), Product.id.desc())
            .limit(fetch)
        )
        add(db.execute(newest).scalars())

    return ids, co_count
