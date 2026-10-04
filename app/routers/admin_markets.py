from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core import cache
from app.core.pagination import PageParams, page_params, paged_rows
from app.database import get_db
from app.dependencies import require_role
from app.models import Category, Product
from app.models.enums import UserRole
from app.models.user import User
from app.services.audit import log_audit

# Where each product is sold (PRD ТЗ№1 §16): one screen to see and change it for many products at once.
router = APIRouter(prefix="/admin/markets", tags=["admin-markets"])
_ROLE = UserRole.PRODUCT_MANAGER


class MarketRow(BaseModel):
    id: int
    name: str
    slug: str
    category_id: int
    category_name: str
    sold_in_countries: Optional[list[str]] = None
    hidden_in_countries: Optional[list[str]] = None


class BulkIn(BaseModel):
    product_ids: list[int] = Field(min_length=1, max_length=2000)
    # Omit a field to leave it alone; [] (or null) clears it, meaning "no restriction".
    sold_in_countries: Optional[list[str]] = None
    hidden_in_countries: Optional[list[str]] = None
    set_sold: bool = False
    set_hidden: bool = False


def _clean(values: Optional[list[str]]) -> Optional[list[str]]:
    seen: dict = {}
    for v in values or []:
        v = v.strip()
        if v:
            seen.setdefault(v.lower(), v)
    return sorted(seen.values()) or None


@router.get("/", response_model=list[MarketRow])
def list_market_rows(
    response: Response,
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    restricted_only: bool = False,
    params: PageParams = Depends(page_params),
    user: User = Depends(require_role(_ROLE)),
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = select(Product, Category.name).join(Category, Category.id == Product.category_id).order_by(Product.id.desc())
    if q:
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(Product.name).like(like), func.lower(Product.slug).like(like)))
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if restricted_only:
        stmt = stmt.where(or_(Product.sold_in_countries.is_not(None), Product.hidden_in_countries.is_not(None)))
    count_stmt = select(Product.id).where(*stmt._where_criteria)
    rows = paged_rows(db, response, stmt, count_stmt, params)
    return [
        {"id": p.id, "name": p.name, "slug": p.slug, "category_id": p.category_id, "category_name": cname,
         "sold_in_countries": p.sold_in_countries, "hidden_in_countries": p.hidden_in_countries}
        for p, cname in rows
    ]


@router.put("/bulk")
def bulk_set(payload: BulkIn, user: User = Depends(require_role(_ROLE)), db: Session = Depends(get_db)) -> dict:
    """Sets the sold-in and/or hidden-in lists on many products at once."""
    if not (payload.set_sold or payload.set_hidden):
        raise HTTPException(status_code=400, detail="Nothing to change")
    products = db.execute(select(Product).where(Product.id.in_(payload.product_ids))).scalars().all()
    if not products:
        raise HTTPException(status_code=404, detail="No such products")
    sold, hidden = _clean(payload.sold_in_countries), _clean(payload.hidden_in_countries)
    for p in products:
        if payload.set_sold:
            p.sold_in_countries = sold
        if payload.set_hidden:
            p.hidden_in_countries = hidden
    log_audit(
        db, user, "markets_bulk_update", "product", len(products),
        new={"products": len(products), "sold_in": sold if payload.set_sold else "unchanged", "hidden_in": hidden if payload.set_hidden else "unchanged"},
    )
    db.commit()
    cache.invalidate("catalog")
    return {"updated": len(products)}
