from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.audit import log_audit
from app.dependencies import require_role
from app.models import SKU
from app.models.enums import UserRole
from app.models.user import User
from app.models.quantity_price_tier import QuantityPriceTier
from app.models.sku_bundle_item import SkuBundleItem
from app.schemas.product import SKUBundleIn, SKUOut, SKUTiersIn, SKUUpdate

router = APIRouter(prefix="/admin/skus", tags=["admin-skus"])


@router.put("/{sku_id}/tiers", response_model=SKUOut)
def replace_quantity_tiers(
    sku_id: int,
    payload: SKUTiersIn,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> SKU:
    """Sets the SKU's quantity-break prices (PRD ТЗ№2 §15, e.g. 10-49 at X, 50+ at Y).
    The posted list replaces the existing one; an empty list removes all tiers."""
    try:
        sku = db.get(SKU, sku_id)
        if sku is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

        old = [{"min_quantity": t.min_quantity, "price": t.price} for t in sku.quantity_tiers]
        sku.quantity_tiers = [QuantityPriceTier(min_quantity=t.min_quantity, price=t.price) for t in payload.tiers]
        log_audit(db, user, "sku_tiers_update", "sku", sku.id, {"tiers": old}, {"tiers": [t.model_dump() for t in payload.tiers]})
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save quantity tiers") from exc

    db.refresh(sku)
    return sku


@router.patch("/{sku_id}", response_model=SKUOut)
def update_sku(
    sku_id: int,
    payload: SKUUpdate,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> SKU:
    try:
        sku = db.get(SKU, sku_id)
        if sku is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

        changes = payload.model_dump(exclude_unset=True)
        log_audit(
            db, user, "sku_update", "sku", sku.id,
            {f: getattr(sku, f) for f in changes}, changes,
        )
        for field, value in changes.items():
            setattr(sku, field, value)

        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Barcode already exists") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update SKU") from exc

    db.refresh(sku)
    return sku


class SKUCost(BaseModel):
    cost_price: Optional[Decimal] = Field(default=None, ge=0, description="Cost of one unit in the SKU's own currency; null clears it")


@router.get("/{sku_id}/cost", response_model=SKUCost)
def get_sku_cost(
    sku_id: int, user: User = Depends(require_role(UserRole.PRODUCT_MANAGER, UserRole.ACCOUNTANT)), db: Session = Depends(get_db)
) -> SKUCost:
    sku = db.get(SKU, sku_id)
    if sku is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")
    return SKUCost(cost_price=sku.cost_price)


@router.put("/{sku_id}/cost", response_model=SKUCost)
def set_sku_cost(
    sku_id: int,
    payload: SKUCost,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER, UserRole.ACCOUNTANT)),
    db: Session = Depends(get_db),
) -> SKUCost:
    sku = db.get(SKU, sku_id)
    if sku is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")
    log_audit(db, user, "sku_cost_update", "sku", sku.id, {"cost_price": sku.cost_price}, {"cost_price": payload.cost_price})
    sku.cost_price = payload.cost_price
    db.commit()
    return SKUCost(cost_price=sku.cost_price)


@router.put("/{sku_id}/bundle", response_model=SKUOut)
def set_bundle_contents(
    sku_id: int,
    payload: SKUBundleIn,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> SKU:
    """Describes what is inside a set / pack SKU (PRD ТЗ№1 §7). The list replaces the old one; an empty list
    makes it an ordinary SKU again. A set cannot contain itself or another set."""
    sku = db.get(SKU, sku_id)
    if sku is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")
    wanted: dict = {}
    for item in payload.items:
        component = db.execute(select(SKU).where(SKU.sku_code == item.sku_code.strip())).scalar_one_or_none()
        if component is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"SKU {item.sku_code} not found")
        if component.id == sku.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A set cannot contain itself")
        if component.bundle_items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{component.sku_code} is itself a set; sets cannot be nested")
        wanted[component.id] = wanted.get(component.id, 0) + item.quantity
    old = [{"sku": i.sku_code, "quantity": i.quantity} for i in sku.bundle_items]
    sku.bundle_items = [SkuBundleItem(component_sku_id=cid, quantity=qty) for cid, qty in wanted.items()]
    db.flush()
    db.refresh(sku)
    log_audit(db, user, "sku_bundle_update", "sku", sku.id, {"items": old}, {"items": [{"sku": i.sku_code, "quantity": i.quantity} for i in sku.bundle_items]})
    db.commit()
    db.refresh(sku)
    return sku
