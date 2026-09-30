from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import OrderStatus, RefundStatus
from app.models.order import Order
from app.models.refund import Refund
from app.models.user import User
from app.services.analytics import record_event
from app.services.audit import log_audit
from app.services.order_service import set_order_status
from app.services.payment.errors import PaymentProviderError, RefundNotSupportedError
from app.services.payment.registry import get_payment_gateway

# Orders that have actually received money and can still be (partially)
# refunded from it. Anything before PAID never took a payment; RETURNED sits
# between DELIVERED and REFUNDED (PRD ТЗ№2 §60) and can still be refunded.
_REFUNDABLE_STATUSES = {
    OrderStatus.PAID,
    OrderStatus.PROCESSING,
    OrderStatus.PACKED,
    OrderStatus.SHIPPED,
    OrderStatus.IN_TRANSIT,
    OrderStatus.DELIVERED,
    OrderStatus.RETURNED,
    OrderStatus.PARTIALLY_REFUNDED,
}


class RefundError(Exception):
    """Raised for a refund request the router should turn into a 4xx response."""


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def total_refunded(db: Session, order_id: int) -> Decimal:
    result = db.execute(
        select(func.coalesce(func.sum(Refund.amount), 0)).where(
            Refund.order_id == order_id, Refund.status == RefundStatus.COMPLETED
        )
    ).scalar_one()
    return Decimal(result)


def create_refund(db: Session, order: Order, amount: Decimal, reason: str | None, admin_user: User) -> Refund:
    """Refund part or all of a paid order (PRD ТЗ№3 §31/§67, ТЗ№4 §28).
    Raises RefundError for request-shape problems (bad amount, wrong order
    status) that never reach the provider. A provider-side failure is
    recorded as a FAILED Refund row and re-raised so the caller still sees
    an error, but the row stays for audit/reconciliation."""
    if order.status not in _REFUNDABLE_STATUSES:
        raise RefundError(f"Order in status {order.status.value} cannot be refunded")

    already_refunded = total_refunded(db, order.id)
    if already_refunded + amount > order.total_amount:
        raise RefundError(
            f"Refund of {amount} would exceed the order total "
            f"({already_refunded} already refunded of {order.total_amount})"
        )

    refund = Refund(
        order_id=order.id,
        amount=amount,
        currency=order.currency,
        reason=reason,
        provider=order.payment_method,
        status=RefundStatus.PENDING,
        created_by_user_id=admin_user.id,
    )
    db.add(refund)
    db.flush()

    try:
        gateway = get_payment_gateway(order.payment_method)
        provider_refund_id = gateway.refund(order, amount)
    except (RefundNotSupportedError, PaymentProviderError) as exc:
        refund.status = RefundStatus.FAILED
        refund.failure_reason = str(exc)
        log_audit(db, admin_user, "refund_failed", "order", order.id, None, {"amount": str(amount), "error": str(exc)})
        db.commit()
        raise RefundError(str(exc)) from exc

    refund.status = RefundStatus.COMPLETED
    refund.provider_refund_id = provider_refund_id
    refund.completed_at = _now()

    new_total_refunded = already_refunded + amount
    target_status = (
        OrderStatus.REFUNDED if new_total_refunded >= order.total_amount else OrderStatus.PARTIALLY_REFUNDED
    )
    if order.status != target_status:
        set_order_status(db, order, target_status, admin_user, note=f"Refund of {amount} {order.currency}")

    log_audit(
        db,
        admin_user,
        "refund_completed",
        "order",
        order.id,
        None,
        {"amount": str(amount), "provider_refund_id": provider_refund_id},
    )
    db.commit()
    record_event(
        db, "refund", user=order.user, session_id=order.guest_order_token,
        order_id=order.id, value=str(amount), currency=order.currency,
    )
    db.refresh(refund)
    return refund
