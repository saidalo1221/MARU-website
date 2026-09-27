from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.order import Order
from app.models.quote_request import QuoteRequest, QuoteStatus
from app.models.user import User
from app.schemas.extras import ConvertQuoteToOrderRequest, QuoteOut, QuoteUpdate
from app.schemas.order import OrderOut
from app.services.audit import log_audit
from app.services.quote_service import QuoteConversionError, convert_quote_to_order

router = APIRouter(prefix="/admin/quotes", tags=["admin-quotes"])


@router.get("/", response_model=list[QuoteOut])
def list_quotes(
    status_filter: QuoteStatus | None = None,
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
) -> list[QuoteRequest]:
    stmt = select(QuoteRequest).order_by(QuoteRequest.id.desc())
    if status_filter is not None:
        stmt = stmt.where(QuoteRequest.status == status_filter)
    return list(db.execute(stmt).scalars().all())


@router.get("/{quote_id}", response_model=QuoteOut)
def get_quote(
    quote_id: int,
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
) -> QuoteRequest:
    quote = db.get(QuoteRequest, quote_id)
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    return quote


@router.patch("/{quote_id}", response_model=QuoteOut)
def update_quote(
    quote_id: int,
    payload: QuoteUpdate,
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
) -> QuoteRequest:
    quote = db.get(QuoteRequest, quote_id)
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")

    changes = payload.model_dump(exclude_unset=True)
    try:
        log_audit(db, user, "quote_update", "quote", quote.id, {f: getattr(quote, f) for f in changes}, changes)
        for field, value in changes.items():
            setattr(quote, field, value)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update quote") from exc
    db.refresh(quote)
    return quote


@router.post("/{quote_id}/convert", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def convert_quote(
    quote_id: int,
    payload: ConvertQuoteToOrderRequest,
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
) -> Order:
    """PRD ТЗ№4 §16/§85: an ACCEPTED quote becomes an order at the quoted
    price. The quote's price is a snapshot; this never re-reads today's
    price list."""
    quote = db.get(QuoteRequest, quote_id)
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")

    try:
        order = convert_quote_to_order(db, quote, payload, user)
    except QuoteConversionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to convert quote to order") from exc

    return order
