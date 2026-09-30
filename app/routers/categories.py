from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.models import Category
from app.schemas.category import CategoryOut
from app.services.i18n import get_category_translations

router = APIRouter(prefix="/categories", tags=["categories"], dependencies=[Depends(rate_limit("categories", 120, 60))])


@router.get("/", response_model=list[CategoryOut])
def list_categories(lang: Optional[str] = None, db: Session = Depends(get_db)) -> list[CategoryOut]:
    """Return the full category tree (PRD section 5: Category -> Series -> ...).
    Pass ?lang=ru|uz|en to get translated names (PRD section 15), falling back
    to the base name where no translation has been entered."""
    try:
        categories = db.execute(select(Category)).scalars().all()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch categories") from exc

    translations = get_category_translations(db, [c.id for c in categories], lang) if lang else {}

    nodes = {
        c.id: CategoryOut(id=c.id, name=translations.get(c.id, c.name), slug=c.slug, parent_id=c.parent_id, children=[])
        for c in categories
    }

    roots: list[CategoryOut] = []
    for c in categories:
        node = nodes[c.id]
        if c.parent_id is None:
            roots.append(node)
        else:
            parent = nodes.get(c.parent_id)
            if parent is not None:
                parent.children.append(node)

    return roots
