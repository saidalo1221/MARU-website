from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.notification_template import NotificationTemplate
from app.models.user import User
from app.schemas.extras import NotificationTemplateIn, NotificationTemplateOut, NotificationTemplateUpdate
from app.services.audit import log_audit

router = APIRouter(prefix="/admin/notification-templates", tags=["admin-notification-templates"])


@router.get("/", response_model=list[NotificationTemplateOut])
def list_templates(
    event: str | None = None,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> list[NotificationTemplate]:
    stmt = select(NotificationTemplate).order_by(NotificationTemplate.event, NotificationTemplate.locale)
    if event is not None:
        stmt = stmt.where(NotificationTemplate.event == event)
    return list(db.execute(stmt).scalars().all())


@router.post("/", response_model=NotificationTemplateOut, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: NotificationTemplateIn,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> NotificationTemplate:
    template = NotificationTemplate(**payload.model_dump())
    db.add(template)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A template for this event/locale/channel already exists",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create template") from exc
    db.refresh(template)
    return template


@router.get("/{template_id}", response_model=NotificationTemplateOut)
def get_template(
    template_id: int,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> NotificationTemplate:
    template = db.get(NotificationTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


@router.patch("/{template_id}", response_model=NotificationTemplateOut)
def update_template(
    template_id: int,
    payload: NotificationTemplateUpdate,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> NotificationTemplate:
    template = db.get(NotificationTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    changes = payload.model_dump(exclude_unset=True)
    try:
        log_audit(
            db, user, "notification_template_update", "notification_template", template.id,
            {f: getattr(template, f) for f in changes}, changes,
        )
        for field, value in changes.items():
            setattr(template, field, value)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update template") from exc
    db.refresh(template)
    return template
