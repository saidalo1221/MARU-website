from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.models.site_settings import SiteSettings
from app.schemas.site_settings import SiteSettingsOut
from app.services.i18n import get_site_settings_translation

router = APIRouter(prefix="/site-settings", tags=["site-settings"], dependencies=[Depends(rate_limit("site_settings", 240, 60))])


@router.get("", response_model=SiteSettingsOut)
def get_site_settings(lang: Optional[str] = None, db: Session = Depends(get_db)) -> SiteSettingsOut:
    settings_row = db.get(SiteSettings, 1)
    if settings_row is None:
        return SiteSettingsOut(
            phone=None, email=None, address=None, latitude=None, longitude=None, about_title=None, about_body=None
        )

    translation = get_site_settings_translation(db, settings_row.id, lang) if lang else None
    return SiteSettingsOut(
        phone=settings_row.phone,
        email=settings_row.email,
        address=(translation.address if translation and translation.address else settings_row.address),
        latitude=settings_row.latitude,
        longitude=settings_row.longitude,
        about_title=(
            translation.about_title if translation and translation.about_title else settings_row.about_title
        ),
        about_body=(translation.about_body if translation and translation.about_body else settings_row.about_body),
        facebook_url=settings_row.facebook_url,
        instagram_url=settings_row.instagram_url,
        telegram_url=settings_row.telegram_url,
        youtube_url=settings_row.youtube_url,
    )
