"""Inbound merchant webhooks for payment providers whose protocol is inverted
(the provider calls us, rather than us polling them) — Payme and Click
(PRD section 13). Stripe/PayPal don't need an endpoint here since
PaymentGatewayBase.confirm() calls out to them directly.

WRITTEN FROM EACH PROVIDER'S PUBLISHED PROTOCOL, NOT VERIFIED against a live
sandbox account for either — no test credentials were available while
building this. Run a full pay -> webhook -> order-paid cycle against each
provider's test environment, and re-check error codes against their current
merchant docs, before processing real payments.
"""

import base64
import hmac
import hashlib
import time
from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.config import settings
from app.database import get_db
from app.models.click_transaction import ClickTransaction
from app.models.enums import OrderStatus
from app.models.order import Order
from app.models.payme_transaction import PaymeTransaction
from app.schemas.order import PaymentMethodOut
from app.services.payment.registry import list_payment_methods
from app.services.order_service import InsufficientStockError, set_order_status

router = APIRouter(prefix="/payments", tags=["payment-webhooks"])


def _now_ms() -> int:
    return int(time.time() * 1000)


@router.get(
    "/methods",
    response_model=list[PaymentMethodOut],
    tags=["payments"],
    dependencies=[Depends(rate_limit("payment_methods", 120, 60))],
)
def payment_methods() -> list[dict]:
    """Frontend-safe capabilities list; secrets are never exposed."""
    return list_payment_methods()


# ===========================================================================
# Payme — https://developer.help.paycom.uz/ (merchant JSON-RPC protocol)
# ===========================================================================

_PAYME_ERROR = {
    "METHOD_NOT_FOUND": -32601,
    "INSUFFICIENT_PRIVILEGE": -32504,
    "INVALID_AMOUNT": -31001,
    "TRANSACTION_NOT_FOUND": -31003,
    "UNABLE_TO_CANCEL": -31007,
    "UNABLE_TO_PERFORM": -31008,
    "ORDER_NOT_FOUND": -31050,
    "ORDER_ALREADY_PAID": -31051,
}

_PAYME_TRANSACTION_TIMEOUT_MS = 43_200_000  # 12 hours


def _payme_error(rpc_id, code: int, message: str) -> dict:
    return {"error": {"code": code, "message": {"ru": message, "uz": message, "en": message}}, "id": rpc_id}


def _payme_result(rpc_id, result: dict) -> dict:
    return {"result": result, "id": rpc_id}


@router.post("/payme/webhook")
async def payme_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    body = await request.json()
    rpc_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {}) or {}

    expected_auth = "Basic " + base64.b64encode(f"Paycom:{settings.PAYME_KEY}".encode()).decode()
    if not settings.PAYME_KEY or request.headers.get("Authorization") != expected_auth:
        return _payme_error(rpc_id, _PAYME_ERROR["INSUFFICIENT_PRIVILEGE"], "Invalid authorization")

    handlers = {
        "CheckPerformTransaction": _payme_check_perform_transaction,
        "CreateTransaction": _payme_create_transaction,
        "PerformTransaction": _payme_perform_transaction,
        "CancelTransaction": _payme_cancel_transaction,
        "CheckTransaction": _payme_check_transaction,
        "GetStatement": _payme_get_statement,
    }
    handler = handlers.get(method)
    if handler is None:
        return _payme_error(rpc_id, _PAYME_ERROR["METHOD_NOT_FOUND"], "Method not found")
    return handler(db, rpc_id, params)


def _payme_order(db: Session, params: dict) -> Order | None:
    order_id = params.get("account", {}).get("order_id")
    if order_id is None:
        return None
    try:
        return db.get(Order, int(order_id))
    except (TypeError, ValueError):
        return None


_PAYME_RETRYABLE_STATUSES = (OrderStatus.NEW, OrderStatus.PAYMENT_PENDING, OrderStatus.PAYMENT_FAILED)


def _payme_check_perform_transaction(db: Session, rpc_id, params: dict) -> dict:
    order = _payme_order(db, params)
    if order is None:
        return _payme_error(rpc_id, _PAYME_ERROR["ORDER_NOT_FOUND"], "Order not found")
    if order.status not in _PAYME_RETRYABLE_STATUSES:
        return _payme_error(rpc_id, _PAYME_ERROR["ORDER_ALREADY_PAID"], "Order already paid or cancelled")
    if int(params.get("amount", 0)) != int(order.total_amount * 100):
        return _payme_error(rpc_id, _PAYME_ERROR["INVALID_AMOUNT"], "Incorrect amount")
    return _payme_result(rpc_id, {"allow": True})


def _payme_create_transaction(db: Session, rpc_id, params: dict) -> dict:
    payme_id = params.get("id")
    try:
        payme_time_ms = int(params["time"])
    except (KeyError, TypeError, ValueError):
        return _payme_error(rpc_id, _PAYME_ERROR["UNABLE_TO_PERFORM"], "Invalid transaction time")
    if not payme_id or payme_time_ms <= 0:
        return _payme_error(rpc_id, _PAYME_ERROR["UNABLE_TO_PERFORM"], "Invalid transaction")
    existing = db.execute(
        select(PaymeTransaction).where(PaymeTransaction.payme_id == payme_id)
    ).scalar_one_or_none()
    if existing is not None:
        return _payme_result(
            rpc_id, {"create_time": existing.create_time_ms, "transaction": str(existing.id), "state": existing.state}
        )

    order = _payme_order(db, params)
    if order is None:
        return _payme_error(rpc_id, _PAYME_ERROR["ORDER_NOT_FOUND"], "Order not found")

    if order.status not in _PAYME_RETRYABLE_STATUSES:
        return _payme_error(rpc_id, _PAYME_ERROR["UNABLE_TO_PERFORM"], "Order cannot be paid")

    active = db.execute(
        select(PaymeTransaction).where(PaymeTransaction.order_id == order.id, PaymeTransaction.state > 0)
    ).scalar_one_or_none()
    if active is not None:
        return _payme_error(rpc_id, _PAYME_ERROR["UNABLE_TO_PERFORM"], "Another transaction is already active")

    if int(params.get("amount", 0)) != int(order.total_amount * 100):
        return _payme_error(rpc_id, _PAYME_ERROR["INVALID_AMOUNT"], "Incorrect amount")

    if order.status in (OrderStatus.NEW, OrderStatus.PAYMENT_FAILED):
        # PAYMENT_FAILED means a prior attempt released the stock reservation
        # (app/services/order_service.py); re-entering PAYMENT_PENDING
        # re-reserves it, which can fail if someone else took the stock meanwhile.
        try:
            set_order_status(db, order, OrderStatus.PAYMENT_PENDING, changed_by=None, note="Payme payment initiated")
        except InsufficientStockError:
            return _payme_error(rpc_id, _PAYME_ERROR["UNABLE_TO_PERFORM"], "Insufficient stock")

    transaction = PaymeTransaction(
        payme_id=payme_id,
        order_id=order.id,
        amount_tiyin=params.get("amount", 0),
        payme_time_ms=payme_time_ms,
        state=1,
        create_time_ms=_now_ms(),
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return _payme_result(rpc_id, {"create_time": transaction.create_time_ms, "transaction": str(transaction.id), "state": 1})


def _payme_perform_transaction(db: Session, rpc_id, params: dict) -> dict:
    transaction = db.execute(
        select(PaymeTransaction).where(PaymeTransaction.payme_id == params.get("id"))
    ).scalar_one_or_none()
    if transaction is None:
        return _payme_error(rpc_id, _PAYME_ERROR["TRANSACTION_NOT_FOUND"], "Transaction not found")

    if transaction.state == 2:
        return _payme_result(
            rpc_id, {"transaction": str(transaction.id), "perform_time": transaction.perform_time_ms, "state": 2}
        )
    if transaction.state != 1:
        return _payme_error(rpc_id, _PAYME_ERROR["UNABLE_TO_PERFORM"], "Transaction is cancelled")

    if _now_ms() - transaction.payme_time_ms > _PAYME_TRANSACTION_TIMEOUT_MS:
        transaction.state = -1
        transaction.reason = 4
        transaction.cancel_time_ms = _now_ms()
        order = db.get(Order, transaction.order_id)
        if order is not None and order.status in (OrderStatus.NEW, OrderStatus.PAYMENT_PENDING):
            set_order_status(db, order, OrderStatus.PAYMENT_FAILED, changed_by=None, note="Payme transaction expired")
        db.commit()
        return _payme_error(rpc_id, _PAYME_ERROR["UNABLE_TO_PERFORM"], "Transaction expired")

    order = db.get(Order, transaction.order_id)
    try:
        set_order_status(db, order, OrderStatus.PAID, changed_by=None, note="Payme payment confirmed")
    except InsufficientStockError:
        transaction.state = -1
        transaction.reason = 5
        transaction.cancel_time_ms = _now_ms()
        db.commit()
        return _payme_error(rpc_id, _PAYME_ERROR["UNABLE_TO_PERFORM"], "Insufficient stock")

    transaction.state = 2
    transaction.perform_time_ms = _now_ms()
    db.commit()
    db.refresh(transaction)
    return _payme_result(rpc_id, {"transaction": str(transaction.id), "perform_time": transaction.perform_time_ms, "state": 2})


def _payme_cancel_transaction(db: Session, rpc_id, params: dict) -> dict:
    transaction = db.execute(
        select(PaymeTransaction).where(PaymeTransaction.payme_id == params.get("id"))
    ).scalar_one_or_none()
    if transaction is None:
        return _payme_error(rpc_id, _PAYME_ERROR["TRANSACTION_NOT_FOUND"], "Transaction not found")

    if transaction.state not in (-1, -2):
        order = db.get(Order, transaction.order_id)
        if transaction.state == 2:
            set_order_status(db, order, OrderStatus.CANCELLED, changed_by=None, note="Payme transaction cancelled")
            transaction.state = -2
        else:
            transaction.state = -1
            if order is not None and order.status in (OrderStatus.NEW, OrderStatus.PAYMENT_PENDING):
                set_order_status(
                    db, order, OrderStatus.PAYMENT_FAILED, changed_by=None, note="Payme transaction cancelled before completion"
                )
        transaction.reason = params.get("reason")
        transaction.cancel_time_ms = _now_ms()
        db.commit()

    return _payme_result(
        rpc_id, {"transaction": str(transaction.id), "cancel_time": transaction.cancel_time_ms, "state": transaction.state}
    )


def _payme_check_transaction(db: Session, rpc_id, params: dict) -> dict:
    transaction = db.execute(
        select(PaymeTransaction).where(PaymeTransaction.payme_id == params.get("id"))
    ).scalar_one_or_none()
    if transaction is None:
        return _payme_error(rpc_id, _PAYME_ERROR["TRANSACTION_NOT_FOUND"], "Transaction not found")

    return _payme_result(
        rpc_id,
        {
            "create_time": transaction.create_time_ms,
            "perform_time": transaction.perform_time_ms,
            "cancel_time": transaction.cancel_time_ms,
            "transaction": str(transaction.id),
            "state": transaction.state,
            "reason": transaction.reason,
        },
    )


def _payme_get_statement(db: Session, rpc_id, params: dict) -> dict:
    rows = (
        db.execute(
            select(PaymeTransaction).where(
                PaymeTransaction.payme_time_ms >= params.get("from", 0),
                PaymeTransaction.payme_time_ms <= params.get("to", _now_ms()),
            )
            .order_by(PaymeTransaction.payme_time_ms.asc())
        )
        .scalars()
        .all()
    )
    return _payme_result(
        rpc_id,
        {
            "transactions": [
                {
                    "id": t.payme_id,
                    "time": t.payme_time_ms,
                    "amount": t.amount_tiyin,
                    "account": {"order_id": str(t.order_id)},
                    "create_time": t.create_time_ms,
                    "perform_time": t.perform_time_ms,
                    "cancel_time": t.cancel_time_ms,
                    "transaction": str(t.id),
                    "state": t.state,
                    "reason": t.reason,
                }
                for t in rows
            ]
        },
    )


# ===========================================================================
# Click — https://docs.click.uz/ (Prepare/Complete webhook protocol)
# ===========================================================================

_CLICK_ERROR = {
    "SUCCESS": 0,
    "SIGN_FAILED": -1,
    "INVALID_AMOUNT": -2,
    "ACTION_NOT_FOUND": -3,
    "ALREADY_PAID": -4,
    "ORDER_NOT_FOUND": -5,
    "TRANSACTION_NOT_FOUND": -6,
    "TRANSACTION_CANCELLED": -9,
}


def _click_response(data: dict, error: int, note: str, **extra) -> dict:
    return {
        "click_trans_id": data.get("click_trans_id"),
        "merchant_trans_id": data.get("merchant_trans_id"),
        "error": error,
        "error_note": note,
        **extra,
    }


def _click_signature_valid(data: dict) -> bool:
    if not settings.CLICK_SECRET_KEY:
        return False

    action = str(data.get("action", ""))
    parts = [
        str(data.get("click_trans_id", "")),
        str(data.get("service_id", "")),
        settings.CLICK_SECRET_KEY,
        str(data.get("merchant_trans_id", "")),
    ]
    if action == "1":
        parts.append(str(data.get("merchant_prepare_id", "")))
    parts += [str(data.get("amount", "")), action, str(data.get("sign_time", ""))]

    expected = hashlib.md5("".join(parts).encode()).hexdigest()
    return hmac.compare_digest(expected, str(data.get("sign_string", "")).lower())


@router.post("/click/webhook")
async def click_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    data = dict(await request.form())

    if not _click_signature_valid(data):
        return _click_response(data, _CLICK_ERROR["SIGN_FAILED"], "SIGN CHECK FAILED")

    if str(data.get("service_id", "")) != str(settings.CLICK_SERVICE_ID):
        return _click_response(data, _CLICK_ERROR["SIGN_FAILED"], "Unknown service")

    merchant_trans_id = data.get("merchant_trans_id", "")
    order = db.get(Order, int(merchant_trans_id)) if merchant_trans_id.isdigit() else None
    if order is None:
        return _click_response(data, _CLICK_ERROR["ORDER_NOT_FOUND"], "Order not found")

    try:
        amount_ok = Decimal(str(data.get("amount", "0"))) == order.total_amount
    except Exception:
        amount_ok = False
    if not amount_ok:
        return _click_response(data, _CLICK_ERROR["INVALID_AMOUNT"], "Incorrect amount")

    action = data.get("action")
    click_trans_id = data.get("click_trans_id")

    if action == "0":
        return _click_prepare(db, data, order, click_trans_id)
    if action == "1":
        return _click_complete(db, data, order, click_trans_id)
    return _click_response(data, _CLICK_ERROR["ACTION_NOT_FOUND"], "Action not found")


def _click_prepare(db: Session, data: dict, order: Order, click_trans_id: str) -> dict:
    transaction = db.execute(
        select(ClickTransaction).where(ClickTransaction.click_trans_id == click_trans_id)
    ).scalar_one_or_none()
    if transaction is None:
        if order.status not in (OrderStatus.NEW, OrderStatus.PAYMENT_PENDING, OrderStatus.PAYMENT_FAILED):
            return _click_response(data, _CLICK_ERROR["ALREADY_PAID"], "Order cannot be paid")
        if order.status in (OrderStatus.NEW, OrderStatus.PAYMENT_FAILED):
            try:
                set_order_status(db, order, OrderStatus.PAYMENT_PENDING, changed_by=None, note="Click payment initiated")
            except InsufficientStockError:
                return _click_response(data, _CLICK_ERROR["ALREADY_PAID"], "Insufficient stock")
        transaction = ClickTransaction(click_trans_id=click_trans_id, order_id=order.id, amount=order.total_amount, action=0)
        db.add(transaction)
        db.commit()
        db.refresh(transaction)

    return _click_response(data, _CLICK_ERROR["SUCCESS"], "Success", merchant_prepare_id=transaction.id)


def _click_complete(db: Session, data: dict, order: Order, click_trans_id: str) -> dict:
    transaction = db.execute(
        select(ClickTransaction).where(ClickTransaction.click_trans_id == click_trans_id)
    ).scalar_one_or_none()
    if transaction is None:
        return _click_response(data, _CLICK_ERROR["TRANSACTION_NOT_FOUND"], "Transaction not found")

    if str(transaction.id) != str(data.get("merchant_prepare_id", "")):
        return _click_response(data, _CLICK_ERROR["TRANSACTION_NOT_FOUND"], "Prepare transaction not found")

    if int(data.get("error", 0)) < 0:
        transaction.action = -1
        if order.status in (OrderStatus.NEW, OrderStatus.PAYMENT_PENDING):
            set_order_status(db, order, OrderStatus.PAYMENT_FAILED, changed_by=None, note="Click payment failed")
        db.commit()
        return _click_response(
            data, _CLICK_ERROR["TRANSACTION_CANCELLED"], "Transaction cancelled", merchant_confirm_id=transaction.id
        )

    if transaction.action == 1:
        return _click_response(
            data, _CLICK_ERROR["ALREADY_PAID"], "Already paid", merchant_confirm_id=transaction.id
        )

    try:
        set_order_status(db, order, OrderStatus.PAID, changed_by=None, note="Click payment confirmed")
    except InsufficientStockError:
        return _click_response(
            data, _CLICK_ERROR["TRANSACTION_CANCELLED"], "Insufficient stock", merchant_confirm_id=transaction.id
        )

    transaction.action = 1
    db.commit()
    return _click_response(data, _CLICK_ERROR["SUCCESS"], "Success", merchant_confirm_id=transaction.id)
