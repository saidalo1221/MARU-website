from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.about_section import AboutSection
from app.schemas.about_section import AboutSectionOut
from app.services.i18n import get_about_section_translations

router = APIRouter(prefix="/about-sections", tags=["about-sections"])


@router.get("", response_model=list[AboutSectionOut])
def list_about_sections(lang: str | None = None, db: Session = Depends(get_db)) -> list[AboutSectionOut]:
    sections = (
        db.execute(select(AboutSection).order_by(AboutSection.sort_order, AboutSection.id)).scalars().all()
    )
    translations = get_about_section_translations(db, [s.id for s in sections], lang) if lang else {}
    return [
        AboutSectionOut(
            id=s.id,
            title=(translations[s.id].title if s.id in translations else s.title),
            body=(translations[s.id].body if s.id in translations else s.body),
        )
        for s in sections
    ]
