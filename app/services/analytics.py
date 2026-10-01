from typing import Optional
import json
import logging

from sqlalchemy.orm import Session

from app.models.analytics_event import AnalyticsEvent
from app.models.user import User
from app.services.integrations import ga4

logger = logging.getLogger("maru.analytics")


def record_event(db: Session, event_name: str, user: Optional[User] = None, session_id: Optional[str] = None, **properties) -> None:
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
    ga4.forward(event_name, user.id if user is not None else None, session_id, properties, db=db)
