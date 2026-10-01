"""The payments ledger (PRD ТЗ№3 §31, ТЗ№4 §23). Every order status change goes through
set_order_status(), which calls apply_order_status() here, so the ledger follows whichever path
moved the order (Payme/Click webhooks, confirm-payment, admin, refunds, reservation expiry)."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.click_transaction import ClickTransaction
from app.models.enums import OrderStatus, PaymentStatus
from app.models.order import Order
from app.models.payme_transaction import PaymeTransaction
from app.models.payment import Payment
from app.services.audit import log_audit

_OPEN = (PaymentStatus.CREATED, PaymentStatus.PENDING, PaymentStatus.AUTHORIZED)
_DEAD = (PaymentStatus.FAILED, PaymentStatus.CANCELLED)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def latest_payment(db: Session, order: Order) -> Optional[Payment]:
    return db.execute(
        select(Payment).where(Payment.order_id == order.id).order_by(Payment.id.desc()).limit(1)
    ).scalar_one_or_none()


def open_payment(db: Session, order: Order) -> Payment:
    """Starts a new attempt (status CREATED) for the order and mirrors it on the order."""
    attempt = len(db.execute(select(Payment.id).where(Payment.order_id == order.id)).all()) + 1
    payment = Payment(
        order_id=order.id,
        provider=order.payment_method,
        amount=order.total_amount,
        currency=order.currency,
        status=PaymentStatus.CREATED,
        idempotency_key=f"order-{order.id}-{attempt}",
    )
    db.add(payment)
    db.flush()
    order.payment_status = PaymentStatus.CREATED
    return payment


def _provider_transaction_id(db: Session, order: Order) -> Optional[str]:
    """The id the payment provider gave this payment, when we have one. Never a redirect URL or a
    client secret: those are credentials, not identifiers."""
    method = (order.payment_method or "").lower()
    if method == "payme":
        stmt = select(PaymeTransaction.payme_id).where(PaymeTransaction.order_id == order.id).order_by(PaymeTransaction.id.desc()).limit(1)
        return db.execute(stmt).scalar_one_or_none()
    if method == "click":
        stmt = select(ClickTransaction.click_trans_id).where(ClickTransaction.order_id == order.id).order_by(ClickTransaction.id.desc()).limit(1)
        return db.execute(stmt).scalar_one_or_none()
    reference = order.payment_reference or ""
    if "_secret_" in reference:  # Stripe client secret "pi_xxx_secret_yyy" -> the intent id
        return reference.split("_secret_")[0]
    if method == "paypal" and reference and not reference.startswith("http"):
        return reference
    return None


def _set(db: Session, order: Order, payment: Payment, new: PaymentStatus, actor=None) -> None:
    old = payment.status
    order.payment_status = new
    if old == new:
        return
    payment.status = new
    log_audit(
        db, actor, "payment_status_change", "payment", payment.id,
        {"status": old.value}, {"status": new.value, "order_id": order.id},
    )


def apply_order_status(db: Session, order: Order, new_status: OrderStatus, actor=None) -> None:
    payment = latest_payment(db, order)

    if new_status == OrderStatus.PAYMENT_PENDING:
        if payment is None or payment.status in _DEAD or payment.status == PaymentStatus.PAID:
            payment = open_payment(db, order)
        _set(db, order, payment, PaymentStatus.PENDING, actor)
        return

    if payment is None:  # an order that predates the ledger
        payment = open_payment(db, order)

    if new_status == OrderStatus.PAID:
        _set(db, order, payment, PaymentStatus.PAID, actor)
        payment.paid_at = payment.paid_at or _now()
        payment.provider_transaction_id = payment.provider_transaction_id or _provider_transaction_id(db, order)
    elif new_status == OrderStatus.PAYMENT_FAILED and payment.status in _OPEN:
        _set(db, order, payment, PaymentStatus.FAILED, actor)
    elif new_status == OrderStatus.CANCELLED and payment.status in _OPEN:
        _set(db, order, payment, PaymentStatus.CANCELLED, actor)
    elif new_status == OrderStatus.REFUNDED:
        _set(db, order, payment, PaymentStatus.REFUNDED, actor)
    elif new_status == OrderStatus.PARTIALLY_REFUNDED:
        _set(db, order, payment, PaymentStatus.PARTIALLY_REFUNDED, actor)
