import requests
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.dependencies import get_current_user_optional, get_current_user_required, get_or_create_cart
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.enums import OrderStatus
from app.models.order import Order
from app.models.user import User
from app.schemas.order import CheckoutOut, CheckoutRequest, OrderOut, PaymentInitiationOut
from app.services.analytics import record_event
from app.services.crm.bitrix24 import Bitrix24Connector
from app.services.integrations.log import run_with_log
from app.services.notifications.email import EmailNotifier
from app.services.order_service import InsufficientStockError, OrderError, create_order, set_order_status
from app.services.payment.errors import PaymentConfigError
from app.services.payment.registry import (
    ensure_payment_method_configured,
    get_payment_gateway,
    payment_reference_kind,
)

router = APIRouter(prefix="/orders", tags=["orders"])

# Real providers (PRD sections 13, 26, 38) — see each module's docstring for
# what's verified vs. still needs sandbox testing, and .env for required keys.
notifier = EmailNotifier()
crm = Bitrix24Connector()

_CANCELLABLE_STATUSES = {OrderStatus.NEW, OrderStatus.PAYMENT_PENDING, OrderStatus.PAID, OrderStatus.PROCESSING}


def _load_cart_with_items(db: Session, cart_id: int) -> Cart:
    stmt = select(Cart).where(Cart.id == cart_id).options(joinedload(Cart.items).joinedload(CartItem.sku))
    return db.execute(stmt).unique().scalar_one()


def _load_order(db: Session, order_id: int) -> Order | None:
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(joinedload(Order.items), joinedload(Order.status_history))
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def _require_order_access(order: Order, user: User | None, order_token: str | None) -> None:
    """Protect customer orders without requiring an account for guest checkout."""
    if order.user_id is not None:
        allowed = user is not None and order.user_id == user.id
    else:
        # The random token is returned once at checkout and must be stored by
        # the frontend (for example in session storage) for guest order pages.
        import hmac

        allowed = bool(order_token and order.guest_order_token and hmac.compare_digest(order.guest_order_token, order_token))
    if not allowed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")


@router.post(
    "/",
    response_model=CheckoutOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("checkout", 20, 60))],
)
def checkout(
    payload: CheckoutRequest,
    cart: Cart = Depends(get_or_create_cart),
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> CheckoutOut:
    cart = _load_cart_with_items(db, cart.id)
    try:
        # Check configuration before mutating the cart/order. Network errors
        # are rolled back below because create_order no longer commits itself.
        ensure_payment_method_configured(payload.payment_method)
        order = create_order(db, cart, payload, user)
        gateway = get_payment_gateway(payload.payment_method)
        order.payment_reference = gateway.create_intent(order)
        db.commit()
    except OrderError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except InsufficientStockError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PaymentConfigError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create order") from exc
    except requests.RequestException as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Payment provider error") from exc

    order = _load_order(db, order.id)
    notifier.order_created(order, db=db)
    run_with_log(db, "crm_bitrix24", "push_order", "order", order.id, lambda: crm.push_order(order))
    record_event(
        db, "begin_checkout", user=user, session_id=order.guest_order_token,
        order_id=order.id, value=str(order.total_amount), currency=order.currency,
    )
    db.commit()
    return CheckoutOut(
        **OrderOut.model_validate(order).model_dump(),
        payment=PaymentInitiationOut(
            method=payload.payment_method,
            reference_kind=payment_reference_kind(payload.payment_method),
            reference=order.payment_reference or "",
        ),
        guest_order_token=order.guest_order_token,
    )


@router.get("/me", response_model=list[OrderOut], dependencies=[Depends(rate_limit("orders_me", 60, 60))])
def list_my_orders(user: User = Depends(get_current_user_required), db: Session = Depends(get_db)) -> list[Order]:
    try:
        orders = (
            db.execute(
                select(Order)
                .where(Order.user_id == user.id)
                .options(joinedload(Order.items), joinedload(Order.status_history))
                .order_by(Order.id.desc())
            )
            .unique()
            .scalars()
            .all()
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch orders") from exc

    return list(orders)


@router.get("/me/{order_id}", response_model=OrderOut, dependencies=[Depends(rate_limit("orders_me", 60, 60))])
def get_my_order(
    order_id: int, user: User = Depends(get_current_user_required), db: Session = Depends(get_db)
) -> Order:
    order = _load_order(db, order_id)
    if order is None or order.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.get("/{order_id}", response_model=OrderOut, dependencies=[Depends(rate_limit("order_lookup", 30, 60))])
def get_order_for_customer(
    order_id: int,
    order_token: str | None = Header(default=None, alias="X-Order-Token"),
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Order:
    order = _load_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    _require_order_access(order, user, order_token)
    return order


@router.post(
    "/{order_id}/confirm-payment",
    response_model=OrderOut,
    dependencies=[Depends(rate_limit("confirm_payment", 20, 60))],
)
def confirm_payment(
    order_id: int,
    order_token: str | None = Header(default=None, alias="X-Order-Token"),
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Order:
    """For Stripe/PayPal, polls the gateway for a completed payment. Payme and
    Click never confirm here — they push status changes via their own
    inbound webhooks (app/routers/payment_webhooks.py), so this always
    returns 402 for orders paid with those two."""
    order = _load_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    _require_order_access(order, user, order_token)

    try:
        gateway = get_payment_gateway(order.payment_method)
        confirmed = gateway.confirm(order.payment_reference or "")
    except PaymentConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Payment provider error") from exc

    if not confirmed:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Payment not confirmed")

    old_status = order.status
    try:
        order = set_order_status(db, order, OrderStatus.PAID, user, note="Payment confirmed")
    except InsufficientStockError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update order status") from exc

    notifier.order_status_changed(order, old_status.value, OrderStatus.PAID.value, db=db)
    order = _load_order(db, order.id)
    run_with_log(db, "crm_bitrix24", "push_order", "order", order.id, lambda: crm.push_order(order))
    db.commit()
    return order


@router.post(
    "/{order_id}/cancel",
    response_model=OrderOut,
    dependencies=[Depends(rate_limit("order_cancel", 10, 60))],
)
def cancel_order(
    order_id: int,
    order_token: str | None = Header(default=None, alias="X-Order-Token"),
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Order:
    order = _load_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    _require_order_access(order, user, order_token)

    if order.status not in _CANCELLABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel an order in status {order.status.value}",
        )

    old_status = order.status
    try:
        order = set_order_status(db, order, OrderStatus.CANCELLED, user, note="Cancelled")
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to cancel order") from exc

    notifier.order_status_changed(order, old_status.value, OrderStatus.CANCELLED.value, db=db)
    order = _load_order(db, order.id)
    run_with_log(db, "crm_bitrix24", "push_order", "order", order.id, lambda: crm.push_order(order))
    db.commit()
    return order
