from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification_template import NotificationTemplate

DEFAULT_LOCALE = "en"


def _find(db: Session, event: str, locale: str, channel: str) -> NotificationTemplate | None:
    return db.execute(
        select(NotificationTemplate).where(
            NotificationTemplate.event == event,
            NotificationTemplate.locale == locale,
            NotificationTemplate.channel == channel,
            NotificationTemplate.is_active.is_(True),
        )
    ).scalar_one_or_none()


def render_template(
    db: Session | None, event: str, context: dict, locale: str = DEFAULT_LOCALE, channel: str = "email"
) -> tuple[str, str] | None:
    """Looks up an admin-managed template (PRD ТЗ№4 §42) for `event`/`locale`/
    `channel`, falling back to the English template, then to None so the
    caller uses its own hardcoded copy. Never raises: a missing placeholder
    in a badly-edited template means "use the hardcoded fallback", not a
    500 on an otherwise-successful order/payment."""
    if db is None:
        return None

    row = _find(db, event, locale, channel)
    if row is None and locale != DEFAULT_LOCALE:
        row = _find(db, event, DEFAULT_LOCALE, channel)
    if row is None:
        return None

    try:
        subject = row.subject.format(**context) if row.subject else ""
        body = row.body.format(**context)
    except (KeyError, IndexError, ValueError):
        return None
    return subject, body
