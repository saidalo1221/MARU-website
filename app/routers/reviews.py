from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.dependencies import get_current_user_required
from app.models import SKU, Product
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product_variant import ProductVariant
from app.models.review import Review, ReviewStatus
from app.models.user import User
from app.schemas.extras import FeaturedReviewOut, ReviewCreate, ReviewOut, ReviewSummary
from app.services.i18n import get_product_translations
from app.services.order_service import _RESERVED_STATUSES

router = APIRouter(prefix="/products", tags=["reviews"])
featured_router = APIRouter(prefix="/reviews", tags=["reviews"])


@featured_router.get(
    "/featured", response_model=list[FeaturedReviewOut], dependencies=[Depends(rate_limit("reviews_featured", 120, 60))]
)
def featured_reviews(
    lang: Optional[str] = None, limit: int = Query(default=6, ge=1, le=12), db: Session = Depends(get_db)
) -> list[FeaturedReviewOut]:
    """Latest approved reviews that have text, for the home page (PRD ТЗ№2 §8.9).
    Only the reviewer's first name is exposed."""
    rows = db.execute(
        select(Review, User.first_name, Product)
        .join(User, User.id == Review.user_id)
        .join(Product, Product.id == Review.product_id)
        .where(Review.status == ReviewStatus.APPROVED, Review.content.is_not(None), Review.content != "")
        .order_by(Review.id.desc())
        .limit(limit)
    ).all()
    translations = get_product_translations(db, [p.id for _, _, p in rows], lang) if lang else {}
    return [
        FeaturedReviewOut(
            id=review.id,
            rating=review.rating,
            content=review.content,
            author=first_name or None,
            product_name=translations[product.id].name if product.id in translations else product.name,
            product_slug=product.slug,
        )
        for review, first_name, product in rows
    ]


def _get_product(db: Session, slug: str) -> Product:
    product = db.execute(select(Product).where(Product.slug == slug)).scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.get("/{slug}/reviews", response_model=ReviewSummary, dependencies=[Depends(rate_limit("reviews_read", 120, 60))])
def list_reviews(slug: str, db: Session = Depends(get_db)) -> ReviewSummary:
    product = _get_product(db, slug)
    reviews = list(
        db.execute(
            select(Review)
            .where(Review.product_id == product.id, Review.status == ReviewStatus.APPROVED)
            .order_by(Review.id.desc())
        ).scalars()
    )
    average = round(sum(r.rating for r in reviews) / len(reviews), 2) if reviews else None
    return ReviewSummary(average_rating=average, count=len(reviews), reviews=reviews)


@router.post(
    "/{slug}/reviews",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("review_create", 10, 3600))],
)
def create_review(
    slug: str,
    payload: ReviewCreate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> Review:
    """Only customers with a paid order containing this product may review it;
    the review stays pending until a marketing manager approves it."""
    product = _get_product(db, slug)
    purchased = db.execute(
        select(func.count())
        .select_from(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .join(SKU, SKU.id == OrderItem.sku_id)
        .join(ProductVariant, ProductVariant.id == SKU.variant_id)
        .where(
            Order.user_id == user.id,
            Order.status.in_(_RESERVED_STATUSES),
            ProductVariant.product_id == product.id,
        )
    ).scalar_one()
    if not purchased:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only customers who bought this product can review it"
        )

    review = Review(user_id=user.id, product_id=product.id, rating=payload.rating, content=payload.content)
    try:
        db.add(review)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already reviewed this product") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save review") from exc
    db.refresh(review)
    return review
