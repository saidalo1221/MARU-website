from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import Inventory, ProductVariant, SKU, Warehouse
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.product import ProductVariantOut, ProductVariantUpdate, SKUCreate, SKUOut

router = APIRouter(prefix="/admin/variants", tags=["admin-variants"])


@router.patch("/{variant_id}", response_model=ProductVariantOut)
def update_variant(
    variant_id: int,
    payload: ProductVariantUpdate,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> ProductVariant:
    try:
        variant = db.get(ProductVariant, variant_id)
        if variant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(variant, field, value)

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update variant") from exc

    db.refresh(variant)
    return variant


@router.post("/{variant_id}/skus", response_model=SKUOut, status_code=status.HTTP_201_CREATED)
def create_sku(
    variant_id: int,
    payload: SKUCreate,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> SKU:
    if db.get(ProductVariant, variant_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

    # Every sellable SKU needs a stock ledger row (PRD section 19), and since
    # Inventory now belongs to a specific warehouse (PRD ТЗ№3 §28), there must
    # be at least one to create it against.
    default_warehouse = db.execute(
        select(Warehouse).where(Warehouse.is_active.is_(True)).order_by(Warehouse.priority.asc())
    ).scalars().first()
    if default_warehouse is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active warehouse exists yet — create one via /admin/warehouses/ before adding SKUs",
        )

    sku = SKU(variant_id=variant_id, **payload.model_dump())
    db.add(sku)
    try:
        db.flush()
        # admin_inventory assumes this row already exists and 404s on GET/PATCH if it doesn't.
        db.add(Inventory(sku_id=sku.id, warehouse_id=default_warehouse.id))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="SKU code or barcode already exists"
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create SKU") from exc

    db.refresh(sku)
    return sku
