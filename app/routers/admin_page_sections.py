from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.page_section import PageSection
from app.models.page_section_translation import PageSectionTranslation
from app.models.user import User
from app.schemas.page_section import (
    PageKey,
    PageSectionAdminOut,
    PageSectionCreate,
    PageSectionMove,
    PageSectionTranslationIn,
    PageSectionTranslationOut,
    PageSectionUpdate,
)
from app.services.i18n import get_page_section_translation, get_page_section_translations

router = APIRouter(prefix="/admin/page-sections", tags=["admin-page-sections"])


def _ordered(db: Session, page: str) -> list[PageSection]:
    return list(
        db.execute(
            select(PageSection).where(PageSection.page == page).order_by(PageSection.sort_order, PageSection.id)
        )
        .scalars()
        .all()
    )


def _to_out(section: PageSection, display_title: Optional[str] = None) -> PageSectionAdminOut:
    return PageSectionAdminOut(
        id=section.id,
        page=section.page,
        title=section.title,
        body=section.body,
        display_title=display_title or section.title,
        sort_order=section.sort_order,
        created_at=section.created_at,
        updated_at=section.updated_at,
    )


@router.get("", response_model=list[PageSectionAdminOut])
def list_sections(
    page: PageKey,
    lang: Optional[str] = None,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> list[PageSectionAdminOut]:
    sections = _ordered(db, page)
    translations = get_page_section_translations(db, [s.id for s in sections], lang) if lang else {}
    return [_to_out(s, translations[s.id].title if s.id in translations else None) for s in sections]


@router.post("", response_model=PageSectionAdminOut, status_code=status.HTTP_201_CREATED)
def create_section(
    payload: PageSectionCreate,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> PageSectionAdminOut:
    max_order = db.execute(
        select(PageSection.sort_order).where(PageSection.page == payload.page).order_by(PageSection.sort_order.desc())
    ).scalars().first()
    section = PageSection(**payload.model_dump(), sort_order=(max_order or 0) + 1)
    db.add(section)
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create section") from exc
    db.refresh(section)
    return _to_out(section)


@router.patch("/{section_id}", response_model=PageSectionAdminOut)
def update_section(
    section_id: int,
    payload: PageSectionUpdate,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> PageSectionAdminOut:
    section = db.get(PageSection, section_id)
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
    section = db.get(PageSection, section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    try:
        db.delete(section)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete section") from exc


@router.post("/{section_id}/move", response_model=list[PageSectionAdminOut])
def move_section(
    section_id: int,
    payload: PageSectionMove,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> list[PageSectionAdminOut]:
    """Swaps this section's sort_order with its immediate neighbor *within
    the same page* — mirrors admin_about_sections.py's move_section()."""
    section = db.get(PageSection, section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    sections = _ordered(db, section.page)
    index = next(i for i, s in enumerate(sections) if s.id == section_id)

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

    return [_to_out(s) for s in _ordered(db, section.page)]


@router.get("/{section_id}/translations", response_model=list[PageSectionTranslationOut])
def list_translations(
    section_id: int,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> list[PageSectionTranslation]:
    if db.get(PageSection, section_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    return list(
        db.execute(select(PageSectionTranslation).where(PageSectionTranslation.section_id == section_id))
        .scalars()
        .all()
    )


@router.put("/{section_id}/translations/{locale}", response_model=PageSectionTranslationOut)
def upsert_translation(
    section_id: int,
    locale: Literal["ru", "uz", "en"],
    payload: PageSectionTranslationIn,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> PageSectionTranslation:
    if db.get(PageSection, section_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    try:
        translation = get_page_section_translation(db, section_id, locale)
        if translation is None:
            translation = PageSectionTranslation(section_id=section_id, locale=locale, **payload.model_dump())
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
