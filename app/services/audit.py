from typing import Optional
import json

from sqlalchemy.orm import Session

from app.core.request_id import client_ip_var, request_id_var
from app.models.audit_log import AuditLog
from app.models.user import User


def log_audit(db: Session, user: Optional[User], action: str, entity: str, entity_id, old=None, new=None) -> None:
    """Add an audit row to the caller's transaction; the caller commits."""
    db.add(
        AuditLog(
            user_id=user.id if user is not None else None,
            action=action,
            entity=entity,
            entity_id=str(entity_id),
            old_value=json.dumps(old, default=str) if old is not None else None,
            new_value=json.dumps(new, default=str) if new is not None else None,
            ip_address=client_ip_var.get(),
            request_id=(request_id_var.get() if request_id_var.get() != "-" else None),
        )
    )


def audit_create(db: Session, user: Optional[User], action: str, entity: str, obj, data=None) -> None:
    """Flushes so `obj` has an id, then logs its creation in the caller's transaction."""
    db.flush()
    log_audit(db, user, action, entity, obj.id, None, data)


def audit_update(db: Session, user: Optional[User], action: str, entity: str, obj, changes: dict) -> None:
    """Call BEFORE applying `changes`: records the old and new value of each changed field."""
    log_audit(db, user, action, entity, obj.id, {f: getattr(obj, f) for f in changes}, changes)

