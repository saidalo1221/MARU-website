from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.models import Category
from app.schemas.category import CategoryOut, CategoryPageOut, CategoryRef
from app.services.i18n import get_category_translation_row, get_category_translations

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


@router.get("/{slug}", response_model=CategoryPageOut)
def get_category_page(slug: str, lang: Optional[str] = None, db: Session = Depends(get_db)) -> CategoryPageOut:
    """One category with its page content, in the requested language where an
    override exists (PRD ТЗ№2 §10: heading, description, image, SEO text)."""
    category = db.execute(select(Category).where(Category.slug == slug)).scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    related = [category] + ([category.parent] if category.parent is not None else []) + list(category.children)
    names = get_category_translations(db, [c.id for c in related], lang) if lang else {}
    translation = get_category_translation_row(db, category.id, lang) if lang else None

    def ref(c: Category) -> CategoryRef:
        return CategoryRef(id=c.id, name=names.get(c.id, c.name), slug=c.slug)

    return CategoryPageOut(
        id=category.id,
        name=names.get(category.id, category.name),
        slug=category.slug,
        description=(translation.description if translation and translation.description else category.description),
        seo_content=(translation.seo_content if translation and translation.seo_content else category.seo_content),
        image_url=category.image_url,
        parent=ref(category.parent) if category.parent is not None else None,
        children=[ref(c) for c in sorted(category.children, key=lambda c: c.name)],
    )
