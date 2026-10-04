"""Stock reconciliation (PRD ТЗ№4 §26, §68-69).

`Inventory.reserved` is a running counter changed on every order transition; if
a crash or a manual DB edit ever skips one, it drifts. This recomputes what
`reserved` should be from the orders themselves (each order item holds its
quantity at its warehouse while the order is in a reserving status) and reports
the differences. Reporting is the default; fixing is opt-in."""

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.order import Order
from app.models.order_item import OrderItem
from app.services.order_service import _RESERVED_STATUSES


@dataclass
class StockMismatch:
    inventory_id: int
    sku_id: int
    warehouse_id: int
    stock: int
    reserved: int
    expected_reserved: int

    @property
    def problem(self) -> str:
        if self.reserved != self.expected_reserved:
            return "reserved_drift"
        return "oversold"  # reserved is right but exceeds stock


def find_mismatches(db: Session) -> list[StockMismatch]:
    held = {
        (sku_id, warehouse_id): qty
        for sku_id, warehouse_id, qty in db.execute(
            select(OrderItem.sku_id, OrderItem.warehouse_id, func.sum(OrderItem.quantity))
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.status.in_(_RESERVED_STATUSES), OrderItem.sku_id.is_not(None), OrderItem.warehouse_id.is_not(None))
            .group_by(OrderItem.sku_id, OrderItem.warehouse_id)
        ).all()
    }
    mismatches = []
    for inv in db.execute(select(Inventory)).scalars().all():
        expected = int(held.get((inv.sku_id, inv.warehouse_id), 0))
        if inv.reserved != expected or inv.reserved > inv.stock:
            mismatches.append(StockMismatch(inv.id, inv.sku_id, inv.warehouse_id, inv.stock, inv.reserved, expected))
    return mismatches


def fix_reserved_drift(db: Session, mismatches: Optional[list[StockMismatch]] = None) -> int:
    """Sets `reserved` back to the value the orders imply. Only drift is fixed;
    an oversold row (reserved > stock) needs a human - stock is physical."""
    fixed = 0
    for m in mismatches if mismatches is not None else find_mismatches(db):
        if m.problem != "reserved_drift":
            continue
        inv = db.get(Inventory, m.inventory_id)
        inv.reserved = m.expected_reserved
        fixed += 1
    db.commit()
    return fixed
