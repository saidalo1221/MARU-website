from typing import Optional
import json
import logging

from sqlalchemy.orm import Session

from app.models.analytics_event import AnalyticsEvent
from app.core.request_id import analytics_consent_var
from app.models.user import User
from app.services.integrations import ga4, meta

logger = logging.getLogger("maru.analytics")


def record_event(
    db: Session, event_name: str, user: Optional[User] = None, session_id: Optional[str] = None,
    forward_ads: Optional[bool] = None, **properties
) -> None:
    """Records one PRD ТЗ№4 §46 event. Never raises and never rolls back the
    caller's transaction — an analytics write failing must not fail the
    checkout/login/etc. it's describing (same isolation principle as
    notifications/CRM push, PRD §78). After storing, the event is forwarded to
    GA4 when configured (integrations/ga4.py)."""
    try:
        db.add(
            AnalyticsEvent(
                event_name=event_name,
                user_id=user.id if user is not None else None,
                session_id=session_id,
                properties=json.dumps(properties, default=str) if properties else None,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to record analytics event %s", event_name)
        return
    # Ad platforms only hear about visitors who agreed to analytics (the cookie banner); an event raised outside a
    # request (a payment callback) carries the choice the visitor made when ordering via `forward_ads`.
    if forward_ads is None:
        forward_ads = analytics_consent_var.get()
    if not forward_ads:
        return
    ga4.forward(event_name, user.id if user is not None else None, session_id, properties, db=db)
    meta.forward(event_name, user.id if user is not None else None, session_id, properties, db=db)
