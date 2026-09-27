from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.dependencies import get_current_user_optional
from app.models.quote_request import QuoteRequest
from app.models.user import User
from app.schemas.extras import QuoteCreate, QuoteOut
from app.services.analytics import record_event
from app.services.crm.bitrix24 import Bitrix24Connector
from app.services.integrations.log import run_with_log

router = APIRouter(prefix="/quotes", tags=["quotes"])
crm = Bitrix24Connector()


@router.post(
    "/",
    response_model=QuoteOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("quotes", 5, 3600))],
)
def create_quote(
    payload: QuoteCreate,
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> QuoteRequest:
    """Public Request a Quote / wholesale / distributor form (PRD ТЗ№2 §32-33)."""
    quote = QuoteRequest(**payload.model_dump(), user_id=user.id if user is not None else None)
    try:
        db.add(quote)
        db.flush()
        quote.rfq_number = f"RFQ-{datetime.now(timezone.utc).year}-{quote.id:06d}"
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to submit request") from exc

    db.refresh(quote)
    run_with_log(db, "crm_bitrix24", "push_quote", "quote", quote.id, lambda: crm.push_quote(quote))
    record_event(db, "generate_lead", user=user, quote_id=quote.id, request_type=quote.request_type)
    db.commit()
    return quote
