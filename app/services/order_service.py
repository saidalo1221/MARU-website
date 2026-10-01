import json
from typing import Optional
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from secrets import token_urlsafe
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.cart import Cart
from app.models.enums import CustomerType, OrderStatus
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory
from app.models.promo_code import PromoCode
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.order import CheckoutRequest
from app.services import outbound_webhooks, payment_ledger
from app.services.integrations import events as integration_events
from app.services.analytics import record_event
from app.services.audit import log_audit
from app.services.currency import CurrencyError, convert_amount
from app.services.pricing import (
    PromoCodeError,
    promo_line_discounts,
    record_redemption,
    redeem_promo,
    resolve_unit_price,
    validate_promo,
)
from app.services.shipping import ShippingError, calculate_shipping, cart_weight_g
from app.services.tax import calculate_lines_tax


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


ATTRIBUTION_KEYS = ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "referrer", "landing_page")


def clean_attribution(raw: Optional[dict]) -> Optional[str]:
    """Keeps only known string keys, each capped at 255 chars, as a JSON string
    (or None when nothing usable was sent). Client-supplied, so never trusted
    beyond being stored and displayed as text."""
    if not raw:
        return None
    kept = {k: str(raw[k])[:255] for k in ATTRIBUTION_KEYS if raw.get(k) not in (None, "")}
    return json.dumps(kept) if kept else None


class OrderError(Exception):
    """Raised for checkout failures the router turns into a 4xx response."""


class InvalidTransitionError(Exception):
    """Raised when an admin status change isn't allowed by the order state machine."""


def validate_transition(old_status: OrderStatus, new_status: OrderStatus) -> None:
    if old_status != new_status and new_status not in _ALLOWED_TRANSITIONS.get(old_status, set()):
        raise InvalidTransitionError(f"Cannot move order from {old_status.value} to {new_status.value}")


class InsufficientStockError(Exception):
    """Raised when a reserving transition can't reserve enough stock for an item."""


# Reservation happens as soon as an order enters one of these statuses from a
# non-reserved status (PRD ТЗ№3 §19/§63: reservation happens on order
# creation, not on payment). NEW covers order creation; PAYMENT_PENDING and
# PAID cover retrying payment on an order that previously lost its
# reservation (PAYMENT_FAILED/CANCELLED) without starting a new checkout.
_RESERVING_STATUSES = {OrderStatus.NEW, OrderStatus.PAYMENT_PENDING, OrderStatus.PAID}
_RESERVED_STATUSES = {
    OrderStatus.NEW,
    OrderStatus.PAYMENT_PENDING,
    OrderStatus.PAID,
    OrderStatus.PROCESSING,
    OrderStatus.PACKED,
    OrderStatus.SHIPPED,
    OrderStatus.IN_TRANSIT,
    OrderStatus.DELIVERED,
    # A partial refund does not release stock — the order is still being
    # fulfilled for whatever wasn't refunded.
    OrderStatus.PARTIALLY_REFUNDED,
}
_ALLOWED_TRANSITIONS = {
    OrderStatus.NEW: {OrderStatus.PAYMENT_PENDING, OrderStatus.PAID, OrderStatus.CANCELLED, OrderStatus.PAYMENT_FAILED},
    OrderStatus.PAYMENT_PENDING: {
        OrderStatus.NEW,
        OrderStatus.PAID,
        OrderStatus.CANCELLED,
        OrderStatus.PAYMENT_FAILED,
    },
    OrderStatus.PAYMENT_FAILED: {OrderStatus.NEW, OrderStatus.PAYMENT_PENDING, OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {
        OrderStatus.PROCESSING,
        OrderStatus.CANCELLED,
        OrderStatus.REFUNDED,
        OrderStatus.PARTIALLY_REFUNDED,
    },
    OrderStatus.PROCESSING: {
        OrderStatus.PACKED,
        OrderStatus.CANCELLED,
        OrderStatus.REFUNDED,
        OrderStatus.PARTIALLY_REFUNDED,
    },
    OrderStatus.PACKED: {
        OrderStatus.SHIPPED,
        OrderStatus.CANCELLED,
        OrderStatus.REFUNDED,
        OrderStatus.PARTIALLY_REFUNDED,
    },
    OrderStatus.SHIPPED: {
        OrderStatus.IN_TRANSIT,
        OrderStatus.DELIVERED,
        OrderStatus.RETURNED,
        OrderStatus.PARTIALLY_REFUNDED,
    },
    OrderStatus.IN_TRANSIT: {OrderStatus.DELIVERED, OrderStatus.RETURNED, OrderStatus.PARTIALLY_REFUNDED},
    OrderStatus.DELIVERED: {OrderStatus.RETURNED, OrderStatus.REFUNDED, OrderStatus.PARTIALLY_REFUNDED},
    OrderStatus.RETURNED: {OrderStatus.REFUNDED},
    OrderStatus.PARTIALLY_REFUNDED: {OrderStatus.REFUNDED},
    OrderStatus.CANCELLED: set(),
    OrderStatus.REFUNDED: set(),
}
_RELEASING_STATUSES = {OrderStatus.CANCELLED, OrderStatus.RETURNED, OrderStatus.REFUNDED, OrderStatus.PAYMENT_FAILED}


def available_stock(db: Session, sku_id: int) -> int:
    """Aggregate availability across every active warehouse (PRD ТЗ№3 §68).
    This is only a pre-check for "is it worth trying" — _reserve_stock()
    below is the atomic, authoritative check, and it reserves from a single
    warehouse per line rather than splitting across warehouses, so a
    positive aggregate here does not guarantee a reservation will succeed."""
    rows = db.execute(
        select(Inventory)
        .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
        .where(Inventory.sku_id == sku_id, Warehouse.is_active.is_(True))
    ).scalars().all()
    return sum(row.available for row in rows)


def expire_stale_reservations(db: Session) -> int:
    """Release stock and cancel any NEW/PAYMENT_PENDING order whose
    reservation TTL has passed (PRD ТЗ№3 §19/§63) — this is what stops two
    guests from indefinitely holding the last units of stock without either
    of them paying. Called opportunistically from create_order() and by
    app/tasks/expire_reservations.py, which should be scheduled (cron/systemd
    timer) since this project has no task queue yet. Commits per order so one
    bad row can't block the rest; returns the number of orders expired."""
    stale_orders = (
        db.execute(
            select(Order).where(
                Order.status.in_([OrderStatus.NEW, OrderStatus.PAYMENT_PENDING]),
                Order.reservation_expires_at.is_not(None),
                Order.reservation_expires_at < _now(),
            )
        )
        .scalars()
        .all()
    )
    expired = 0
    for order in stale_orders:
        try:
            set_order_status(db, order, OrderStatus.CANCELLED, changed_by=None, note="Reservation expired (TTL)")
            expired += 1
        except Exception:
            db.rollback()
    return expired


def _unit_cost_usd(db: Session, sku) -> Optional[Decimal]:
    """The SKU's cost converted to USD, or None when no cost is set or no rate exists."""
    if sku.cost_price is None:
        return None
    try:
        return convert_amount(db, sku.cost_price, sku.currency, "USD")
    except CurrencyError:
        return None


def generate_order_number() -> str:
    return f"MARU-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:6].upper()}"


def create_order(db: Session, cart: Cart, checkout: CheckoutRequest, user: Optional[User]) -> Order:
    if not cart.items:
        raise OrderError("Cart is empty")

    # Best-effort: free up anyone else's lapsed reservations before checking
    # availability, so an abandoned checkout doesn't starve this one. Never
    # blocks checkout on its own failure.
    try:
        expire_stale_reservations(db)
    except Exception:
        db.rollback()

    customer_type = user.customer_type if user is not None else CustomerType.RETAIL

    subtotal = Decimal("0")
    line_data = []
    for item in cart.items:
        if available_stock(db, item.sku_id) < item.quantity:
            raise OrderError(f"INSUFFICIENT_STOCK: not enough stock for SKU {item.sku.sku_code}")
        minimum = item.sku.variant.product.min_order_quantity or 1
        if item.quantity < minimum:
            raise OrderError(
                f"MIN_ORDER_QUANTITY: SKU {item.sku.sku_code} requires at least {minimum} units"
            )
        try:
            unit_price = resolve_unit_price(db, item.sku, customer_type, item.quantity, cart.currency)
        except CurrencyError as exc:
            raise OrderError(str(exc)) from exc
        line_total = unit_price * item.quantity
        subtotal += line_total
        line_data.append((item, unit_price, line_total))

    promo: Optional[PromoCode] = None
    if checkout.promo_code:
        try:
            promo = validate_promo(
                db, checkout.promo_code, subtotal, cart.currency,
                lines=[(item.sku, total) for item, _price, total in line_data],
                user_id=user.id if user is not None else None, email=checkout.email,
            )
        except PromoCodeError as exc:
            raise OrderError(str(exc)) from exc

    try:
        line_discounts = promo_line_discounts(db, promo, [(item.sku, total) for item, _price, total in line_data], cart.currency)
    except PromoCodeError as exc:
        raise OrderError(str(exc)) from exc
    discount = sum(line_discounts, Decimal("0"))
    # PRD §69 pricing pipeline: ... Discount -> Tax -> Shipping -> Total.
    # Tax is computed on the post-discount merchandise subtotal; shipping
    # itself is not taxed (PRD doesn't specify shipping being taxable).
    line_taxes = calculate_lines_tax(
        db, checkout.country, customer_type.value,
        [(item.sku.variant.product.tax_class, total - line_discounts[i]) for i, (item, _price, total) in enumerate(line_data)],
        region=checkout.region, currency=cart.currency,
    )
    tax = sum(line_taxes, Decimal("0"))
    try:
        delivery = calculate_shipping(
            db, checkout.country, checkout.delivery_method, cart_weight_g(cart), subtotal - discount, cart.currency
        )
    except ShippingError as exc:
        raise OrderError(str(exc)) from exc
    total = subtotal + delivery + tax - discount

    order = Order(
        order_number=generate_order_number(),
        user_id=user.id if user is not None else None,
        guest_order_token=token_urlsafe(32) if user is None else None,
        cart_id=cart.id,
        promo_code_id=promo.id if promo is not None else None,
        promo_code_snapshot=promo.code if promo is not None else None,
        status=OrderStatus.NEW,
        customer_type_snapshot=customer_type.value,
        currency=cart.currency,
        subtotal_amount=subtotal,
        discount_amount=discount,
        tax_amount=tax,
        delivery_amount=delivery,
        total_amount=total,
        order_type=checkout.order_type,
        first_name=checkout.first_name,
        last_name=checkout.last_name,
        phone=checkout.phone,
        email=checkout.email,
        country=checkout.country,
        region=checkout.region,
        city=checkout.city,
        address_line=checkout.address_line,
        postal_code=checkout.postal_code,
        delivery_method=checkout.delivery_method,
        payment_method=checkout.payment_method,
        language=checkout.language,
        whatsapp_opt_in=checkout.whatsapp_opt_in,
        source=checkout.source,
        company_name=checkout.company_name,
        company_reg_number=checkout.company_reg_number,
        company_tax_number=checkout.company_tax_number,
        company_address=checkout.company_address,
        contact_person=checkout.contact_person,
        attribution=clean_attribution(checkout.attribution),
    )
    db.add(order)
    db.flush()  # need order.id before inserting items/history

    # Appended to order.items (rather than db.add per row) so the in-memory
    # relationship is populated for _reserve_stock() below without a re-query.
    for index, (item, unit_price, line_total) in enumerate(line_data):
        order.items.append(
            OrderItem(
                discount_amount=line_discounts[index],
                unit_cost_usd=_unit_cost_usd(db, item.sku),
                tax_amount=line_taxes[index],
                sku_id=item.sku_id,
                sku_code_snapshot=item.sku.sku_code,
                product_name_snapshot=item.sku.variant.product.name,
                variant_name_snapshot=item.sku.variant.name,
                unit_price=unit_price,
                quantity=item.quantity,
                line_total=line_total,
                currency=cart.currency,
            )
        )

    # Reserve stock now, at creation, not on a later PAID transition (PRD
    # ТЗ№3 §19/§63) — raises InsufficientStockError under a row lock if two
    # checkouts race for the last units. The caller must roll back on error.
    _reserve_stock(db, order)
    order.reservation_expires_at = _now() + timedelta(minutes=settings.RESERVATION_TTL_MINUTES)

    db.add(
        OrderStatusHistory(
            order_id=order.id,
            from_status=None,
            to_status=OrderStatus.NEW,
            changed_by_user_id=user.id if user is not None else None,
        )
    )

    if promo is not None:
        try:
            redeem_promo(db, promo)
        except PromoCodeError as exc:
            raise OrderError(str(exc)) from exc
        record_redemption(db, promo, order, user.id if user is not None else None, checkout.email)

    cart.is_active = False
    cart.converted_at = _now()
    # Keep a signed-in customer's saved-for-later lines: they were not bought, so
    # they move to a fresh active cart instead of staying on the converted one.
    if cart.user_id is not None and cart.saved_items:
        carried = Cart(user_id=cart.user_id, currency=cart.currency)
        db.add(carried)
        db.flush()
        for saved in list(cart.saved_items):
            saved.cart_id = carried.id

    # The caller creates the provider payment intent in the same transaction.
    # A configuration or provider failure can therefore roll everything back
    # without consuming the customer's cart, promo usage, or reservation.
    db.flush()
    payment_ledger.open_payment(db, order)
    return order


def set_order_status(
    db: Session,
    order: Order,
    new_status: OrderStatus,
    changed_by: Optional[User],
    note: Optional[str] = None,
) -> Order:
    old_status = order.status
    if old_status == new_status:
        return order

    if new_status in _RESERVING_STATUSES and old_status not in _RESERVED_STATUSES:
        _reserve_stock(db, order)
    elif new_status in _RELEASING_STATUSES and old_status in _RESERVED_STATUSES:
        _release_stock(db, order)

    # Only NEW/PAYMENT_PENDING/PAYMENT_FAILED are subject to the expiry
    # sweep; every other status either holds its reservation indefinitely
    # (paid and beyond) or has already released it.
    order.reservation_expires_at = (
        _now() + timedelta(minutes=settings.RESERVATION_TTL_MINUTES)
        if new_status in (OrderStatus.NEW, OrderStatus.PAYMENT_PENDING)
        else None
    )

    order.status = new_status
    payment_ledger.apply_order_status(db, order, new_status, changed_by)
    log_audit(
        db, changed_by, "order_status_change", "order", order.id, {"status": old_status.value}, {"status": new_status.value}
    )
    db.add(
        OrderStatusHistory(
            order_id=order.id,
            from_status=old_status,
            to_status=new_status,
            changed_by_user_id=changed_by.id if changed_by is not None else None,
            note=note,
        )
    )
    db.commit()
    db.refresh(order)

    if new_status == OrderStatus.PAID:
        # Single choke point for "purchase" (PRD ТЗ№4 §46) regardless of which
        # gateway/path got the order here (confirm_payment, Payme/Click
        # webhooks, admin override) — see app/services/analytics.py.
        record_event(
            db, "purchase", user=order.user, session_id=order.guest_order_token,
            order_id=order.id, value=str(order.total_amount), currency=order.currency,
        )
        integration_events.emit(db, integration_events.ORDER_PAID, order, commit=True)
    elif new_status == OrderStatus.CANCELLED:
        integration_events.emit(db, integration_events.ORDER_CANCELLED, order, commit=True)
    for event in outbound_webhooks.STATUS_EVENTS.get(new_status.name, ()):
        outbound_webhooks.emit_for_order(db, event, order)
    return order


def _lock_ordered_items(order: Order) -> list[OrderItem]:
    """Items in a stable (sku_id) order. Inventory rows are locked one line at
    a time (FOR UPDATE), so two concurrent orders touching the same SKUs in
    opposite cart order would otherwise deadlock on InnoDB (MariaDB aborts one
    with error 1213). SQLite serialises writers and never shows this."""
    return sorted(order.items, key=lambda item: item.sku_id or 0)


def _reserve_stock(db: Session, order: Order) -> None:
    """PRD ТЗ№3 §68: with multiple warehouses, picks exactly one warehouse
    per line — the highest-priority (lowest Warehouse.priority) active
    warehouse that alone has enough available stock for that line — rather
    than splitting one line across warehouses. §68 explicitly allows manual
    priority as sufficient for phase 1; it does not require split
    fulfillment, which this does not attempt. If no single warehouse can
    cover a line (even when the sum across warehouses could), this raises
    even though available_stock() might have looked sufficient."""
    for item in _lock_ordered_items(order):
        if item.sku_id is None:
            continue
        candidates = db.execute(
            select(Inventory)
            .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
            .where(Inventory.sku_id == item.sku_id, Warehouse.is_active.is_(True))
            .order_by(Warehouse.priority.asc())
            .with_for_update()
        ).scalars().all()
        inventory = next((row for row in candidates if row.available >= item.quantity), None)
        if inventory is None:
            raise InsufficientStockError(f"Insufficient stock for SKU {item.sku_code_snapshot}")
        inventory.reserved += item.quantity
        item.warehouse_id = inventory.warehouse_id


def _release_stock(db: Session, order: Order) -> None:
    for item in _lock_ordered_items(order):
        if item.sku_id is None or item.warehouse_id is None:
            continue
        inventory = db.execute(
            select(Inventory)
            .where(Inventory.sku_id == item.sku_id, Inventory.warehouse_id == item.warehouse_id)
            .with_for_update()
        ).scalar_one_or_none()
        if inventory is not None:
            inventory.reserved = max(0, inventory.reserved - item.quantity)
