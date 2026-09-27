import json

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def log_audit(db: Session, user: User | None, action: str, entity: str, entity_id, old=None, new=None) -> None:
    """Add an audit row to the caller's transaction; the caller commits."""
    db.add(
        AuditLog(
            user_id=user.id if user is not None else None,
            action=action,
            entity=entity,
            entity_id=str(entity_id),
            old_value=json.dumps(old, default=str) if old is not None else None,
            new_value=json.dumps(new, default=str) if new is not None else None,
        )
    )
