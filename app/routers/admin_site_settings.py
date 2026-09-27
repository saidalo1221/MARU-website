from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.site_settings import SiteSettings
from app.models.site_settings_translation import SiteSettingsTranslation
from app.models.user import User
from app.schemas.site_settings import (
    SiteSettingsOut,
    SiteSettingsTranslationIn,
    SiteSettingsTranslationOut,
    SiteSettingsUpdate,
)
from app.services.i18n import get_site_settings_translation

router = APIRouter(prefix="/admin/site-settings", tags=["admin-site-settings"])


def _get_or_create(db: Session) -> SiteSettings:
    settings_row = db.get(SiteSettings, 1)
    if settings_row is None:
        settings_row = SiteSettings(id=1)
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return settings_row


@router.get("", response_model=SiteSettingsOut)
def get_settings(
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> SiteSettings:
    return _get_or_create(db)


@router.patch("", response_model=SiteSettingsOut)
def update_settings(
    payload: SiteSettingsUpdate,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> SiteSettings:
    settings_row = _get_or_create(db)
    try:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(settings_row, field, value)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save site settings") from exc
    db.refresh(settings_row)
    return settings_row


@router.get("/translations", response_model=list[SiteSettingsTranslationOut])
def list_translations(
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> list[SiteSettingsTranslation]:
    settings_row = _get_or_create(db)
    return list(
        db.execute(
            select(SiteSettingsTranslation).where(SiteSettingsTranslation.site_settings_id == settings_row.id)
        )
        .scalars()
        .all()
    )


@router.put("/translations/{locale}", response_model=SiteSettingsTranslationOut)
def upsert_translation(
    locale: Literal["ru", "uz", "en"],
    payload: SiteSettingsTranslationIn,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> SiteSettingsTranslation:
    settings_row = _get_or_create(db)
    try:
        translation = get_site_settings_translation(db, settings_row.id, locale)
        if translation is None:
            translation = SiteSettingsTranslation(
                site_settings_id=settings_row.id, locale=locale, **payload.model_dump()
            )
            db.add(translation)
        else:
            for field, value in payload.model_dump().items():
                setattr(translation, field, value)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save translation") from exc
    db.refresh(translation)
    return translation
