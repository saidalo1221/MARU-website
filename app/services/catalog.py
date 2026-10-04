"""Catalog helpers for the product list: rating summaries and sales counts used
for the `rating` / `popularity` sorts and the product-card rating (PRD ТЗ№2 §11,
ТЗ№3 §53)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Order, OrderItem, ProductVariant, SKU
from app.models.review import Review, ReviewStatus
from app.services.badges import _SOLD_STATUSES

# Whitelist of ?sort= values (ТЗ№3 §53); anything else is rejected with a 400.
SORT_OPTIONS = ("price_asc", "price_desc", "newest", "popularity", "rating")

MAX_PAGE_SIZE = 100


def rating_stats(db: Session, product_ids: list[int]) -> dict[int, tuple[float, int]]:
    """{product_id: (average rating, number of approved reviews)}; products
    without reviews are absent."""
    if not product_ids:
        return {}
    rows = db.execute(
        select(Review.product_id, func.avg(Review.rating), func.count(Review.id))
        .where(Review.product_id.in_(product_ids), Review.status == ReviewStatus.APPROVED)
        .group_by(Review.product_id)
    ).all()
    return {pid: (round(float(avg), 2), int(n)) for pid, avg, n in rows}


def sales_counts(db: Session, product_ids: list[int]) -> dict[int, int]:
    """{product_id: units sold across paid-or-later orders}."""
    if not product_ids:
        return {}
    rows = db.execute(
        select(ProductVariant.product_id, func.coalesce(func.sum(OrderItem.quantity), 0))
        .select_from(OrderItem)
        .join(SKU, SKU.id == OrderItem.sku_id)
        .join(ProductVariant, ProductVariant.id == SKU.variant_id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(ProductVariant.product_id.in_(product_ids), Order.status.in_(_SOLD_STATUSES))
        .group_by(ProductVariant.product_id)
    ).all()
    return {pid: int(n) for pid, n in rows}
