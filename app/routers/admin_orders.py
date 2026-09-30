from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import OrderStatus, UserRole
from app.models.order import Order
from app.models.user import User
from app.schemas.extras import RefundCreate, RefundOut
from app.schemas.order import OrderOut, OrderStatusUpdate
from app.services.notifications.logging import LoggingNotifier
from app.services.order_service import InsufficientStockError, InvalidTransitionError, set_order_status, validate_transition
from app.services.refund_service import RefundError, create_refund

router = APIRouter(prefix="/admin/orders", tags=["admin-orders"])
notifier = LoggingNotifier()


def _load_order(db: Session, order_id: int) -> Optional[Order]:
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(joinedload(Order.items), joinedload(Order.status_history))
    )
    return db.execute(stmt).unique().scalar_one_or_none()


@router.get("/", response_model=list[OrderOut])
def list_orders(
    status_filter: Optional[OrderStatus] = None,
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
) -> list[Order]:
    stmt = (
        select(Order).options(joinedload(Order.items), joinedload(Order.status_history)).order_by(Order.id.desc())
    )
    if status_filter is not None:
        stmt = stmt.where(Order.status == status_filter)

    try:
        orders = db.execute(stmt).unique().scalars().all()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch orders") from exc

    return list(orders)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
) -> Order:
    order = _load_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
) -> Order:
    order = _load_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    old_status = order.status
    try:
        validate_transition(old_status, payload.status)
        order = set_order_status(db, order, payload.status, user, note=payload.note)
    except InvalidTransitionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InsufficientStockError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update order status") from exc

    if old_status != order.status:
        notifier.order_status_changed(order, old_status.value, order.status.value)

    return _load_order(db, order.id)


@router.post("/{order_id}/refund", response_model=RefundOut, status_code=status.HTTP_201_CREATED)
def refund_order(
    order_id: int,
    payload: RefundCreate,
    user: User = Depends(require_role(UserRole.ACCOUNTANT, UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
):
    order = _load_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    old_status = order.status
    try:
        refund = create_refund(db, order, payload.amount, payload.reason, user)
    except RefundError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process refund") from exc

    if old_status != order.status:
        notifier.order_status_changed(order, old_status.value, order.status.value)

    return refund
