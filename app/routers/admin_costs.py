from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.pagination import PageParams, page_params, paged_rows
from app.database import get_db
from app.dependencies import require_role
from app.models import SKU, Product, ProductVariant
from app.models.enums import UserRole
from app.models.user import User
from app.services.audit import log_audit

# What each SKU costs us (PRD ТЗ№1 §59-60 margin): one screen for all SKUs, with a paste-in import for many at once.
router = APIRouter(prefix="/admin/costs", tags=["admin-costs"])
_ROLE = (UserRole.PRODUCT_MANAGER, UserRole.ACCOUNTANT)


class CostRow(BaseModel):
    sku_id: int
    sku_code: str
    product_name: str
    variant_name: str
    currency: str
    retail_price: Decimal
    cost_price: Optional[Decimal] = None
    margin_percent: Optional[float] = None  # (retail - cost) / retail


class CostItem(BaseModel):
    sku_code: str = Field(min_length=1, max_length=100)
    cost_price: Optional[Decimal] = Field(default=None, ge=0, le=Decimal("1000000000"))  # null clears the cost


class BulkCosts(BaseModel):
    items: list[CostItem] = Field(min_length=1, max_length=5000)


@router.get("/", response_model=list[CostRow])
def list_costs(
    response: Response,
    q: Optional[str] = None,
    missing_only: bool = False,
    params: PageParams = Depends(page_params),
    user: User = Depends(require_role(*_ROLE)),
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = (
        select(SKU, Product.name, ProductVariant.name)
        .join(ProductVariant, ProductVariant.id == SKU.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .order_by(SKU.id.desc())
    )
    if q:
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(SKU.sku_code).like(like), func.lower(Product.name).like(like)))
    if missing_only:
        stmt = stmt.where(SKU.cost_price.is_(None))
    count_stmt = select(SKU.id).join(ProductVariant, ProductVariant.id == SKU.variant_id).join(Product, Product.id == ProductVariant.product_id).where(*stmt._where_criteria)
    rows = paged_rows(db, response, stmt, count_stmt, params)
    out = []
    for sku, product_name, variant_name in rows:
        margin = None
        if sku.cost_price is not None and sku.retail_price:
            margin = round(float((sku.retail_price - sku.cost_price) / sku.retail_price * 100), 1)
        out.append({
            "sku_id": sku.id, "sku_code": sku.sku_code, "product_name": product_name, "variant_name": variant_name,
            "currency": sku.currency, "retail_price": sku.retail_price, "cost_price": sku.cost_price, "margin_percent": margin,
        })
    return out


@router.put("/bulk")
def bulk_set_costs(payload: BulkCosts, user: User = Depends(require_role(*_ROLE)), db: Session = Depends(get_db)) -> dict:
    """Sets costs by SKU code (one row or thousands). Unknown codes are reported, not fatal; nothing is half-applied
    for a code that exists. Costs are in each SKU's own currency."""
    codes = {i.sku_code.strip() for i in payload.items}
    by_code = {s.sku_code: s for s in db.execute(select(SKU).where(SKU.sku_code.in_(codes))).scalars()}
    updated, unknown = 0, []
    for item in payload.items:
        sku = by_code.get(item.sku_code.strip())
        if sku is None:
            unknown.append(item.sku_code)
            continue
        if sku.cost_price != item.cost_price:
            sku.cost_price = item.cost_price
            updated += 1
    log_audit(db, user, "sku_cost_bulk_update", "sku", updated, new={"updated": updated, "unknown": unknown[:20]})
    db.commit()
    return {"updated": updated, "unknown": unknown}
