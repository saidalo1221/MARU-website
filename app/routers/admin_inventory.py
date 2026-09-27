from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.audit import log_audit
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.inventory import Inventory
from app.models.sku import SKU
from app.models.user import User
from app.schemas.inventory import InventoryCreate, InventoryOut, InventoryUpdate

router = APIRouter(prefix="/admin/inventory", tags=["admin-inventory"])


def _get_inventory_row(db: Session, sku_id: int, warehouse_id: int) -> Inventory | None:
    return db.execute(
        select(Inventory).where(Inventory.sku_id == sku_id, Inventory.warehouse_id == warehouse_id)
    ).scalar_one_or_none()


@router.get("/{sku_id}", response_model=list[InventoryOut])
def list_inventory_for_sku(
    sku_id: int,
    user: User = Depends(require_role(UserRole.WAREHOUSE_MANAGER)),
    db: Session = Depends(get_db),
) -> list[Inventory]:
    """One row per warehouse holding stock for this SKU (PRD ТЗ№3 §28)."""
    try:
        rows = db.execute(select(Inventory).where(Inventory.sku_id == sku_id)).scalars().all()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch inventory") from exc
    return list(rows)


@router.post("/{sku_id}", response_model=InventoryOut, status_code=status.HTTP_201_CREATED)
def add_inventory_for_warehouse(
    sku_id: int,
    payload: InventoryCreate,
    user: User = Depends(require_role(UserRole.WAREHOUSE_MANAGER)),
    db: Session = Depends(get_db),
) -> Inventory:
    """Starts stocking this SKU at another warehouse. A SKU already has one
    row (its first warehouse) from creation (app/routers/admin_variants.py)."""
    if db.get(SKU, sku_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    inventory = Inventory(sku_id=sku_id, **payload.model_dump())
    db.add(inventory)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This SKU already has inventory at that warehouse"
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create inventory") from exc

    db.refresh(inventory)
    return inventory


@router.get("/{sku_id}/{warehouse_id}", response_model=InventoryOut)
def get_inventory(
    sku_id: int,
    warehouse_id: int,
    user: User = Depends(require_role(UserRole.WAREHOUSE_MANAGER)),
    db: Session = Depends(get_db),
) -> Inventory:
    try:
        inventory = _get_inventory_row(db, sku_id, warehouse_id)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch inventory") from exc

    if inventory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No inventory record for this SKU/warehouse")

    return inventory


@router.patch("/{sku_id}/{warehouse_id}", response_model=InventoryOut)
def update_inventory(
    sku_id: int,
    warehouse_id: int,
    payload: InventoryUpdate,
    user: User = Depends(require_role(UserRole.WAREHOUSE_MANAGER)),
    db: Session = Depends(get_db),
) -> Inventory:
    try:
        inventory = _get_inventory_row(db, sku_id, warehouse_id)
        if inventory is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No inventory record for this SKU/warehouse")

        log_audit(
            db, user, "inventory_update", "inventory", inventory.id,
            {"stock": inventory.stock, "incoming": inventory.incoming, "min_stock": inventory.min_stock},
            payload.model_dump(exclude_unset=True),
        )
        if payload.stock is not None:
            inventory.stock = payload.stock
        if payload.incoming is not None:
            inventory.incoming = payload.incoming
        if payload.min_stock is not None:
            inventory.min_stock = payload.min_stock

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update inventory") from exc

    db.refresh(inventory)
    return inventory
