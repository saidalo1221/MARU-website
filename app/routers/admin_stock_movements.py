from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.pagination import PageParams, page_params, paged
from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.inventory import Inventory
from app.models.sku import SKU
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.models.warehouse import Warehouse
from app.services import outbound_webhooks
from app.services.audit import log_audit

router = APIRouter(prefix="/admin/stock", tags=["admin-stock"])
_ROLE = UserRole.WAREHOUSE_MANAGER


class TransferIn(BaseModel):
    sku_id: Optional[int] = None
    sku_code: Optional[str] = Field(default=None, max_length=100)  # alternative to sku_id
    from_warehouse_id: int
    to_warehouse_id: int
    quantity: int = Field(gt=0, le=1_000_000)
    note: Optional[str] = Field(default=None, max_length=300)


class MovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movement_type: str
    sku_id: int
    from_warehouse_id: Optional[int]
    to_warehouse_id: Optional[int]
    quantity: int
    note: Optional[str]
    created_by_user_id: Optional[int]
    created_at: datetime


def _locked_row(db: Session, sku_id: int, warehouse_id: int) -> Optional[Inventory]:
    # Rows are always locked in warehouse-id order by the caller, so two opposite transfers cannot deadlock.
    return db.execute(
        select(Inventory).where(Inventory.sku_id == sku_id, Inventory.warehouse_id == warehouse_id).with_for_update()
    ).scalar_one_or_none()


@router.post("/transfer", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
def transfer_stock(payload: TransferIn, user: User = Depends(require_role(_ROLE)), db: Session = Depends(get_db)) -> StockMovement:
    """Moves units of one SKU from one warehouse to another. Only stock that is not reserved by an open order
    can move (available = stock - reserved), so a transfer can never take stock away from a paid order."""
    if payload.from_warehouse_id == payload.to_warehouse_id:
        raise HTTPException(status_code=400, detail="Choose two different warehouses")
    if payload.sku_id is None and not payload.sku_code:
        raise HTTPException(status_code=422, detail="Give sku_id or sku_code")
    sku = db.get(SKU, payload.sku_id) if payload.sku_id is not None else db.execute(select(SKU).where(SKU.sku_code == payload.sku_code)).scalar_one_or_none()
    if sku is None:
        raise HTTPException(status_code=404, detail="SKU not found")
    for wid in (payload.from_warehouse_id, payload.to_warehouse_id):
        if db.get(Warehouse, wid) is None:
            raise HTTPException(status_code=404, detail="Warehouse not found")

    first, second = sorted((payload.from_warehouse_id, payload.to_warehouse_id))
    rows = {first: _locked_row(db, sku.id, first), second: _locked_row(db, sku.id, second)}
    source = rows[payload.from_warehouse_id]
    if source is None or source.stock - source.reserved < payload.quantity:
        have = 0 if source is None else max(0, source.stock - source.reserved)
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Only {have} unit(s) are available to move from that warehouse")
    target = rows[payload.to_warehouse_id]
    if target is None:
        target = Inventory(sku_id=sku.id, warehouse_id=payload.to_warehouse_id, stock=0, reserved=0, incoming=0, min_stock=0)
        db.add(target)
    source.stock -= payload.quantity
    target.stock += payload.quantity

    movement = StockMovement(
        movement_type="transfer", sku_id=sku.id, from_warehouse_id=payload.from_warehouse_id,
        to_warehouse_id=payload.to_warehouse_id, quantity=payload.quantity, note=payload.note, created_by_user_id=user.id,
    )
    db.add(movement)
    db.flush()
    log_audit(
        db, user, "stock_transfer", "inventory", sku.id,
        {"from_warehouse": payload.from_warehouse_id, "stock": source.stock + payload.quantity},
        {"to_warehouse": payload.to_warehouse_id, "quantity": payload.quantity},
    )
    db.commit()
    db.refresh(movement)
    for row in (source, target):
        outbound_webhooks.emit(db, "inventory.updated", {
            "sku_id": sku.id, "sku_code": sku.sku_code, "warehouse_id": row.warehouse_id, "stock": row.stock,
            "reserved": row.reserved, "available": max(0, row.stock - row.reserved), "incoming": row.incoming,
        })
    return movement


@router.get("/movements", response_model=list[MovementOut])
def list_movements(
    response: Response,
    sku_id: Optional[int] = None,
    params: PageParams = Depends(page_params),
    user: User = Depends(require_role(_ROLE)),
    db: Session = Depends(get_db),
) -> list[StockMovement]:
    stmt = select(StockMovement).order_by(StockMovement.id.desc())
    if sku_id is not None:
        stmt = stmt.where(StockMovement.sku_id == sku_id)
    return paged(db, response, stmt, stmt, params)
