from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.pagination import PageParams, page_params, paged
from app.database import get_db
from app.dependencies import require_role
from app.models.enums import OrderStatus, PaymentStatus, UserRole
from app.models.payment import Payment
from app.schemas.payment import PaymentOut
from app.models.order import Order
from app.models.shipment import Shipment
from app.models.user import User
from app.schemas.extras import RefundCreate, RefundOut
from app.schemas.order import OrderOut, OrderStatusUpdate
from app.schemas.shipment import ShipmentCreate, ShipmentEventCreate, ShipmentOut, ShipmentUpdate
from app.services.notifications.queued import QueuedNotifier
from app.services.notifications.logging import LoggingNotifier
from app.services.order_service import InsufficientStockError, InvalidTransitionError, set_order_status, validate_transition
from app.services.refund_service import RefundError, create_refund
from app.services.shipment_service import ShipmentError, add_shipment_event, create_shipment, find_order_shipment

router = APIRouter(prefix="/admin/orders", tags=["admin-orders"])
notifier = LoggingNotifier()
# Shipment updates are the one admin action customers must actually hear about.
shipment_notifier = QueuedNotifier()


def _load_order(db: Session, order_id: int) -> Optional[Order]:
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            joinedload(Order.items),
            joinedload(Order.status_history),
            selectinload(Order.shipments).selectinload(Shipment.events),
        )
    )
    return db.execute(stmt).unique().scalar_one_or_none()


@router.get("/", response_model=list[OrderOut])
def list_orders(
    response: Response,
    status_filter: Optional[OrderStatus] = None,
    payment_status: Optional[PaymentStatus] = None,
    params: PageParams = Depends(page_params),
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
) -> list[Order]:
    count_stmt = select(Order.id)
    stmt = (
        select(Order)
        .options(
            joinedload(Order.items),
            joinedload(Order.status_history),
            selectinload(Order.shipments).selectinload(Shipment.events),
        )
        .order_by(Order.id.desc())
    )
    if status_filter is not None:
        stmt = stmt.where(Order.status == status_filter)
        count_stmt = count_stmt.where(Order.status == status_filter)
    if payment_status is not None:
        stmt = stmt.where(Order.payment_status == payment_status)
        count_stmt = count_stmt.where(Order.payment_status == payment_status)

    try:
        orders = paged(db, response, stmt, count_stmt, params, unique=True)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch orders") from exc

    return list(orders)


@router.get("/{order_id}/payments", response_model=list[PaymentOut])
def list_order_payments(
    order_id: int,
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
) -> list[Payment]:
    """Every payment attempt of the order, oldest first (PRD ТЗ№03 §31)."""
    return list(db.execute(select(Payment).where(Payment.order_id == order_id).order_by(Payment.id)).scalars())


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


@router.post("/{order_id}/shipments", response_model=ShipmentOut, status_code=status.HTTP_201_CREATED)
def create_order_shipment(
    order_id: int,
    payload: ShipmentCreate,
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
):
    order = _load_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    try:
        shipment = create_shipment(db, order, payload, user)
    except (ShipmentError, InvalidTransitionError, InsufficientStockError) as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create shipment") from exc
    shipment_notifier.shipment_updated(order, shipment, db=db)
    return shipment


@router.patch("/{order_id}/shipments/{shipment_id}", response_model=ShipmentOut)
def update_order_shipment(
    order_id: int,
    shipment_id: int,
    payload: ShipmentUpdate,
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
):
    order = _load_order(db, order_id)
    shipment = find_order_shipment(order, shipment_id) if order is not None else None
    if shipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    changes = payload.model_dump(exclude_unset=True)
    try:
        for field, value in changes.items():
            setattr(shipment, field, value)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update shipment") from exc
    return shipment


@router.post("/{order_id}/shipments/{shipment_id}/events", response_model=ShipmentOut, status_code=status.HTTP_201_CREATED)
def add_order_shipment_event(
    order_id: int,
    shipment_id: int,
    payload: ShipmentEventCreate,
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
):
    order = _load_order(db, order_id)
    shipment = find_order_shipment(order, shipment_id) if order is not None else None
    if shipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    old_status = shipment.status
    try:
        shipment = add_shipment_event(db, order, shipment, payload, user)
    except (ShipmentError, InvalidTransitionError, InsufficientStockError) as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add shipment event") from exc
    # Location-only updates on the same status are not worth an email.
    if shipment.status != old_status:
        shipment_notifier.shipment_updated(order, shipment, db=db)
    return shipment


@router.post("/{order_id}/refund",response_model=RefundOut, status_code=status.HTTP_201_CREATED)
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
