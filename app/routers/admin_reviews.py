from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.review import Review, ReviewStatus
from app.models.user import User
from app.schemas.extras import ReviewModeration, ReviewOut

router = APIRouter(prefix="/admin/reviews", tags=["admin-reviews"])


@router.get("/", response_model=list[ReviewOut])
def list_reviews(
    status_filter: Optional[ReviewStatus] = None,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> list[Review]:
    stmt = select(Review).order_by(Review.id.desc())
    if status_filter is not None:
        stmt = stmt.where(Review.status == status_filter)
    return list(db.execute(stmt).scalars().all())


@router.patch("/{review_id}", response_model=ReviewOut)
def moderate_review(
    review_id: int,
    payload: ReviewModeration,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> Review:
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    try:
        review.status = payload.status
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update review") from exc
    db.refresh(review)
    return review
