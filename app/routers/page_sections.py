from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.models.page_section import PageSection
from app.schemas.page_section import PageKey, PageSectionOut
from app.services.i18n import get_page_section_translations

router = APIRouter(prefix="/page-sections", tags=["page-sections"], dependencies=[Depends(rate_limit("page_sections", 240, 60))])


@router.get("", response_model=list[PageSectionOut])
def list_page_sections(page: PageKey, lang: Optional[str] = None, db: Session = Depends(get_db)) -> list[PageSectionOut]:
    sections = list(
        db.execute(
            select(PageSection).where(PageSection.page == page).order_by(PageSection.sort_order, PageSection.id)
        )
        .scalars()
        .all()
    )
    translations = get_page_section_translations(db, [s.id for s in sections], lang) if lang else {}
    return [
        PageSectionOut(
            id=s.id,
            title=(translations[s.id].title if s.id in translations else s.title),
            body=(translations[s.id].body if s.id in translations else s.body),
            category=s.category,
        )
        for s in sections
    ]
