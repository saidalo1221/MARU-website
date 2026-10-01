import hmac
import re
from typing import Optional
import requests
from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.rate_limit import rate_limit
from app.core.pagination import PageParams, page_params, paged
from app.database import get_db
from app.dependencies import get_current_user_optional, get_current_user_required, get_or_create_cart
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.enums import OrderStatus
from app.models.order import Order
from app.models.shipment import Shipment
from app.models.user import User
from app.schemas.order import CheckoutOut, CheckoutRequest, OrderOut, PaymentInitiationOut
from app.schemas.shipment import TrackOrderOut, TrackOrderRequest
from app.services.crm.bitrix24 import Bitrix24Connector
from app.services.integrations.log import run_with_log
from app.services import document_generator, outbound_webhooks
from app.services.notifications.queued import QueuedNotifier
from app.services.order_service import InsufficientStockError, OrderError, create_order, set_order_status
from app.services.payment.errors import PaymentConfigError
from app.services.payment.registry import (
    ensure_payment_method_configured,
    method_available_in_country,
    get_payment_gateway,
    payment_reference_kind,
)

router = APIRouter(prefix="/orders", tags=["orders"])

# Real providers (PRD sections 13, 26, 38) — see each module's docstring for
# what's verified vs. still needs sandbox testing, and .env for required keys.
notifier = QueuedNotifier()
crm = Bitrix24Connector()

_CANCELLABLE_STATUSES = {OrderStatus.NEW, OrderStatus.PAYMENT_PENDING, OrderStatus.PAID, OrderStatus.PROCESSING}


_ORDER_LOAD_OPTIONS = (
    joinedload(Order.items),
    joinedload(Order.status_history),
    selectinload(Order.shipments).selectinload(Shipment.events),
)


_IDEMPOTENCY_KEY_RE = re.compile(r"[A-Za-z0-9_\-]{8,64}")


def _find_idempotent_order(db: Session, key: str) -> Optional[Order]:
    return db.execute(select(Order).where(Order.idempotency_key == key).options(*_ORDER_LOAD_OPTIONS)).unique().scalar_one_or_none()


def _owns_idempotent_order(db: Session, order: Order, user: Optional[User], cart_token: Optional[str]) -> bool:
    """Only the original requester may replay a key: the same account, or (for
    guests) the same cart token the original checkout used."""
    if order.user_id is not None:
        return user is not None and user.id == order.user_id
    cart = db.get(Cart, order.cart_id) if order.cart_id is not None else None
    return bool(cart_token and cart is not None and cart.token and hmac.compare_digest(cart.token, cart_token))


def _checkout_out(order: Order) -> CheckoutOut:
    return CheckoutOut(
        **OrderOut.model_validate(order).model_dump(),
        payment=PaymentInitiationOut(
            method=order.payment_method,
            reference_kind=payment_reference_kind(order.payment_method),
            reference=order.payment_reference or "",
        ),
        guest_order_token=order.guest_order_token,
    )


def _replay_or_conflict(db: Session, key: str, user: Optional[User], cart_token: Optional[str], response: Response) -> CheckoutOut:
    existing = _find_idempotent_order(db, key)
    if existing is None:
        raise HTTPException(status_code=500, detail="Failed to create order")
    if not _owns_idempotent_order(db, existing, user, cart_token):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Idempotency-Key already used")
    response.headers["Idempotent-Replayed"] = "true"
    return _checkout_out(existing)


def _load_cart_with_items(db: Session, cart_id: int) -> Cart:
    stmt = select(Cart).where(Cart.id == cart_id).options(joinedload(Cart.items).joinedload(CartItem.sku))
    return db.execute(stmt).unique().scalar_one()


def _load_order(db: Session, order_id: int) -> Optional[Order]:
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(*_ORDER_LOAD_OPTIONS)
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def _require_order_access(order: Order, user: Optional[User], order_token: Optional[str]) -> None:
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
    response: Response,
    cart: Cart = Depends(get_or_create_cart),
    user: Optional[User] = Depends(get_current_user_optional),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    cart_token: Optional[str] = Header(default=None, alias="X-Cart-Token"),
    db: Session = Depends(get_db),
) -> CheckoutOut:
    """An optional `Idempotency-Key` header makes a retried checkout (double
    click, dropped response) return the original order instead of failing on
    the already-converted cart."""
    if idempotency_key is not None:
        if not _IDEMPOTENCY_KEY_RE.fullmatch(idempotency_key):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Idempotency-Key")
        if _find_idempotent_order(db, idempotency_key) is not None:
            return _replay_or_conflict(db, idempotency_key, user, cart_token, response)

    cart = _load_cart_with_items(db, cart.id)
    try:
        # Check configuration before mutating the cart/order. Network errors
        # are rolled back below because create_order no longer commits itself.
        if not method_available_in_country(payload.payment_method, payload.country):
            raise OrderError(f"{payload.payment_method} is not available in {payload.country}")
        ensure_payment_method_configured(payload.payment_method)
        order = create_order(db, cart, payload, user)
        order.idempotency_key = idempotency_key
        gateway = get_payment_gateway(payload.payment_method)
        order.payment_reference = gateway.create_intent(order)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if idempotency_key is not None and _find_idempotent_order(db, idempotency_key) is not None:
            # A concurrent request with the same key won the race.
            return _replay_or_conflict(db, idempotency_key, user, cart_token, response)
        raise HTTPException(status_code=500, detail="Failed to create order") from exc
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
    db.commit()
    outbound_webhooks.emit_for_order(db, "order.created", order)
    document_generator.generate_for_status(db, order, None)
    return _checkout_out(order)


@router.post("/track", response_model=TrackOrderOut, dependencies=[Depends(rate_limit("order_track", 10, 60))])
def track_order(payload: TrackOrderRequest, db: Session = Depends(get_db)) -> Order:
    """Guest-friendly "Track Order" (PRD ТЗ№2 §25): order number + the email on
    the order. Every mismatch returns the same 404 so the endpoint can't be
    used to discover which order numbers or emails exist."""
    order = db.execute(
        select(Order).where(Order.order_number == payload.order_number.strip().upper()).options(*_ORDER_LOAD_OPTIONS)
    ).unique().scalar_one_or_none()
    if order is None or order.email.strip().lower() != payload.email.strip().lower():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.get("/me", response_model=list[OrderOut], dependencies=[Depends(rate_limit("orders_me", 60, 60))])
def list_my_orders(
    response: Response,
    params: PageParams = Depends(page_params),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> list[Order]:
    try:
        orders = paged(
            db,
            response,
            select(Order).where(Order.user_id == user.id).options(*_ORDER_LOAD_OPTIONS).order_by(Order.id.desc()),
            select(Order.id).where(Order.user_id == user.id),
            params,
            unique=True,
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
    order_token: Optional[str] = Header(default=None, alias="X-Order-Token"),
    user: Optional[User] = Depends(get_current_user_optional),
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
    order_token: Optional[str] = Header(default=None, alias="X-Order-Token"),
    user: Optional[User] = Depends(get_current_user_optional),
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


_RETRYABLE_PAYMENT_STATUSES = {OrderStatus.NEW, OrderStatus.PAYMENT_PENDING, OrderStatus.PAYMENT_FAILED}


@router.post(
    "/{order_id}/payment",
    response_model=PaymentInitiationOut,
    dependencies=[Depends(rate_limit("order_payment", 20, 60))],
)
def retry_payment(
    order_id: int,
    order_token: Optional[str] = Header(default=None, alias="X-Order-Token"),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> PaymentInitiationOut:
    """Pay Now / Try Again (PRD ТЗ№2 §24): hands back the payment link for an
    order that is unpaid or whose payment failed. Only redirect-style gateways
    (Payme, Click) can be retried this way - their webhooks already re-reserve
    stock for a failed order; card gateways need a new checkout."""
    order = _load_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    _require_order_access(order, user, order_token)

    if order.status not in _RETRYABLE_PAYMENT_STATUSES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This order is not waiting for payment")
    try:
        kind = payment_reference_kind(order.payment_method)
    except KeyError:
        kind = None
    if kind != "redirect_url" or not order.payment_reference:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment cannot be retried for this order; please place a new order")
    return PaymentInitiationOut(method=order.payment_method, reference_kind=kind, reference=order.payment_reference)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderOut,
    dependencies=[Depends(rate_limit("order_cancel", 10, 60))],
)
def cancel_order(
    order_id: int,
    order_token: Optional[str] = Header(default=None, alias="X-Order-Token"),
    user: Optional[User] = Depends(get_current_user_optional),
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
