"""Admin-editable storefront text (landing page and any other translation key) and per-page SEO tags."""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.site_content import ContentOverride, SeoMeta
from app.models.user import User

Locale = Literal["ru", "uz", "en"]

public = APIRouter(tags=["site-content"], dependencies=[Depends(rate_limit("site_content", 240, 60))])
admin = APIRouter(prefix="/admin", tags=["admin-site-content"])


# ------------------------------------------------------------------ public
@public.get("/content-overrides")
def public_overrides(lang: Locale, db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(ContentOverride).where(ContentOverride.locale == lang)).scalars().all()
    return {r.text_key: r.value for r in rows}


@public.get("/seo-meta")
def public_seo(lang: Locale, db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(SeoMeta).where(SeoMeta.locale == lang)).scalars().all()
    return {
        r.path: {"title": r.title, "description": r.description, "image": r.image_url, "noindex": bool(r.noindex)}
        for r in rows
    }


# ------------------------------------------------------------------- admin
class OverrideIn(BaseModel):
    key: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.]+$")
    locale: Locale
    value: str = Field(max_length=5000)


class OverridesBatch(BaseModel):
    items: list[OverrideIn] = Field(max_length=500)


@admin.get("/content-overrides")
def admin_list_overrides(
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)), db: Session = Depends(get_db)
) -> list[dict]:
    rows = db.execute(select(ContentOverride)).scalars().all()
    return [{"key": r.text_key, "locale": r.locale, "value": r.value} for r in rows]


@admin.put("/content-overrides")
def admin_save_overrides(
    payload: OverridesBatch,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> dict:
    """Saves a batch. An empty value removes the override, so the built-in text shows again."""
    try:
        for item in payload.items:
            row = db.execute(
                select(ContentOverride).where(ContentOverride.text_key == item.key, ContentOverride.locale == item.locale)
            ).scalar_one_or_none()
            if not item.value.strip():
                if row is not None:
                    db.delete(row)
            elif row is None:
                db.add(ContentOverride(text_key=item.key, locale=item.locale, value=item.value))
            else:
                row.value = item.value
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save text") from exc
    return {"saved": len(payload.items)}


class SeoIn(BaseModel):
    path: str = Field(min_length=1, max_length=255, pattern=r"^/[A-Za-z0-9_\-./]*$")
    locale: Locale
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    image_url: Optional[str] = Field(default=None, max_length=500)
    noindex: bool = False


@admin.get("/seo-meta")
def admin_list_seo(
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)), db: Session = Depends(get_db)
) -> list[dict]:
    rows = db.execute(select(SeoMeta)).scalars().all()
    return [
        {"path": r.path, "locale": r.locale, "title": r.title, "description": r.description,
         "image_url": r.image_url, "noindex": bool(r.noindex)}
        for r in rows
    ]


@admin.put("/seo-meta")
def admin_save_seo(
    payload: SeoIn,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> dict:
    """Saves one page/language. With every field cleared the row is removed (the page's own tags apply)."""
    title = (payload.title or "").strip() or None
    description = (payload.description or "").strip() or None
    image = (payload.image_url or "").strip() or None
    row = db.execute(select(SeoMeta).where(SeoMeta.path == payload.path, SeoMeta.locale == payload.locale)).scalar_one_or_none()
    try:
        if not (title or description or image or payload.noindex):
            if row is not None:
                db.delete(row)
        elif row is None:
            db.add(SeoMeta(path=payload.path, locale=payload.locale, title=title, description=description,
                           image_url=image, noindex=payload.noindex))
        else:
            row.title, row.description, row.image_url, row.noindex = title, description, image, payload.noindex
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save SEO tags") from exc
    return {"saved": True}
