from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.about_section import AboutSection
from app.models.about_section_translation import AboutSectionTranslation
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.about_section import (
    AboutSectionAdminOut,
    AboutSectionCreate,
    AboutSectionMove,
    AboutSectionTranslationIn,
    AboutSectionTranslationOut,
    AboutSectionUpdate,
)
from app.services.i18n import get_about_section_translation, get_about_section_translations

router = APIRouter(prefix="/admin/about-sections", tags=["admin-about-sections"])


def _ordered(db: Session) -> list[AboutSection]:
    return list(db.execute(select(AboutSection).order_by(AboutSection.sort_order, AboutSection.id)).scalars().all())


def _to_out(section: AboutSection, display_title: Optional[str] = None) -> AboutSectionAdminOut:
    return AboutSectionAdminOut(
        id=section.id,
        title=section.title,
        body=section.body,
        display_title=display_title or section.title,
        sort_order=section.sort_order,
        created_at=section.created_at,
        updated_at=section.updated_at,
    )


@router.get("", response_model=list[AboutSectionAdminOut])
def list_sections(
    lang: Optional[str] = None,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> list[AboutSectionAdminOut]:
    sections = _ordered(db)
    translations = get_about_section_translations(db, [s.id for s in sections], lang) if lang else {}
    return [_to_out(s, translations[s.id].title if s.id in translations else None) for s in sections]


@router.post("", response_model=AboutSectionAdminOut, status_code=status.HTTP_201_CREATED)
def create_section(
    payload: AboutSectionCreate,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> AboutSectionAdminOut:
    max_order = db.execute(select(AboutSection.sort_order).order_by(AboutSection.sort_order.desc())).scalars().first()
    section = AboutSection(**payload.model_dump(), sort_order=(max_order or 0) + 1)
    db.add(section)
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create section") from exc
    db.refresh(section)
    return _to_out(section)


@router.patch("/{section_id}", response_model=AboutSectionAdminOut)
def update_section(
    section_id: int,
    payload: AboutSectionUpdate,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> AboutSectionAdminOut:
    section = db.get(AboutSection, section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    try:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(section, field, value)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update section") from exc
    db.refresh(section)
    return _to_out(section)


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_section(
    section_id: int,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> None:
    section = db.get(AboutSection, section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    try:
        db.delete(section)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete section") from exc


@router.post("/{section_id}/move", response_model=list[AboutSectionAdminOut])
def move_section(
    section_id: int,
    payload: AboutSectionMove,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> list[AboutSectionAdminOut]:
    """Swaps this section's sort_order with its immediate neighbor — simpler
    and less error-prone than accepting an arbitrary new position from the
    client, and is all a "move up"/"move down" button needs."""
    sections = _ordered(db)
    index = next((i for i, s in enumerate(sections) if s.id == section_id), None)
    if index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    neighbor_index = index - 1 if payload.direction == "up" else index + 1
    if neighbor_index < 0 or neighbor_index >= len(sections):
        return [_to_out(s) for s in sections]

    try:
        sections[index].sort_order, sections[neighbor_index].sort_order = (
            sections[neighbor_index].sort_order,
            sections[index].sort_order,
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to reorder sections") from exc

    return [_to_out(s) for s in _ordered(db)]


@router.get("/{section_id}/translations", response_model=list[AboutSectionTranslationOut])
def list_translations(
    section_id: int,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> list[AboutSectionTranslation]:
    if db.get(AboutSection, section_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    return list(
        db.execute(select(AboutSectionTranslation).where(AboutSectionTranslation.section_id == section_id))
        .scalars()
        .all()
    )


@router.put("/{section_id}/translations/{locale}", response_model=AboutSectionTranslationOut)
def upsert_translation(
    section_id: int,
    locale: Literal["ru", "uz", "en"],
    payload: AboutSectionTranslationIn,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> AboutSectionTranslation:
    if db.get(AboutSection, section_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    try:
        translation = get_about_section_translation(db, section_id, locale)
        if translation is None:
            translation = AboutSectionTranslation(section_id=section_id, locale=locale, **payload.model_dump())
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
