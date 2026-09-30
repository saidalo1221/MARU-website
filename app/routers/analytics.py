import json
from typing import Any, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.dependencies import get_current_user_optional
from app.models.user import User
from app.services.analytics import record_event

router = APIRouter(prefix="/analytics", tags=["analytics"], dependencies=[Depends(rate_limit("analytics", 120, 60))])

MAX_PROPERTIES_BYTES = 2048
RESERVED_KEYS = {"db", "event_name", "user", "session_id"}


class ClientEventIn(BaseModel):
    # Whitelist: only events the browser alone can observe. Server-side events
    # (purchase, add_to_cart, ...) are recorded by their own routers and must
    # not be forgeable from this public endpoint.
    event_name: Literal["view_item", "view_item_list", "search", "view_cart", "add_payment_info", "select_variant"]
    session_id: str | None = Field(default=None, max_length=64)
    properties: dict[str, Any] = Field(default_factory=dict)

    @field_validator("properties")
    @classmethod
    def _limit_properties(cls, v: dict[str, Any]) -> dict[str, Any]:
        if len(json.dumps(v, default=str).encode("utf-8")) > MAX_PROPERTIES_BYTES:
            raise ValueError("properties too large")
        # These would collide with record_event's own parameters.
        if RESERVED_KEYS & v.keys():
            raise ValueError("reserved property name")
        return v


@router.post("/events", status_code=status.HTTP_204_NO_CONTENT)
def ingest_client_event(
    payload: ClientEventIn,
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Response:
    """Public browser-side analytics ingest (PRD ТЗ№4 §46). Capture only;
    record_event never raises, so a failed write is invisible to the client."""
    record_event(db, payload.event_name, user=user, session_id=payload.session_id, **payload.properties)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
