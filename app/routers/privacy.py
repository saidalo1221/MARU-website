"""Self-service personal-data export and account erasure (PRD ТЗ№3 §102).

Erasure anonymizes the account and deletes personal data that exists only
because of the account. Orders and B2B quote requests are deliberately KEPT
(accounting/contract records) - the owner decides whether that is acceptable;
see START_HERE.md."""

import json
from secrets import token_urlsafe
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import delete, or_, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.core.security import hash_password, verify_password
from app.database import get_db
from app.dependencies import get_current_user_required
from app.models.address import Address
from app.models.admin_login_code import AdminLoginCode
from app.models.analytics_event import AnalyticsEvent
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.email_verification_token import EmailVerificationToken
from app.models.enums import OrderStatus, UserRole
from app.models.login_device_code import LoginDeviceCode
from app.models.newsletter_subscriber import NewsletterSubscriber
from app.models.order import Order
from app.models.password_reset_token import PasswordResetToken
from app.models.quote_request import QuoteRequest
from app.models.review import Review
from app.models.stock_alert import StockAlert
from app.models.trusted_device import TrustedDevice
from app.models.user import User
from app.models.wishlist_item import WishlistItem
from app.services.audit import log_audit

router = APIRouter(prefix="/privacy", tags=["privacy"])

# An order in any other status still needs the customer's contact details.
_SETTLED = {OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.RETURNED, OrderStatus.REFUNDED, OrderStatus.PAYMENT_FAILED}

_USER_HIDDEN = {"password_hash", "mfa_secret", "mfa_enabled", "admin_mfa_verified_until", "failed_login_attempts", "locked_until"}
_ORDER_HIDDEN = {"guest_order_token", "payment_reference", "crm_deal_id", "idempotency_key"}


class EraseRequest(BaseModel):
    password: str
    confirm: str  # must be exactly "DELETE"


def _row(obj: Any, hidden: frozenset = frozenset()) -> dict:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns if c.name not in hidden}


@router.get("/export", dependencies=[Depends(rate_limit("privacy_export", 5, 3600))])
def export_my_data(user: User = Depends(get_current_user_required), db: Session = Depends(get_db)) -> Response:
    def rows(model, *conditions):
        return [_row(r) for r in db.execute(select(model).where(*conditions)).scalars().all()]

    orders = db.execute(select(Order).where(Order.user_id == user.id).order_by(Order.id)).scalars().all()
    data = {
        "profile": _row(user, frozenset(_USER_HIDDEN)),
        "addresses": rows(Address, Address.user_id == user.id),
        "orders": [
            {
                **_row(o, frozenset(_ORDER_HIDDEN)),
                "items": [_row(i) for i in o.items],
                "shipments": [{**_row(s), "events": [_row(e) for e in s.events]} for s in o.shipments],
                "status_history": [_row(h) for h in o.status_history],
            }
            for o in orders
        ],
        "wishlist": rows(WishlistItem, WishlistItem.user_id == user.id),
        "reviews": rows(Review, Review.user_id == user.id),
        "quote_requests": rows(QuoteRequest, or_(QuoteRequest.user_id == user.id, QuoteRequest.email == user.email)),
        "stock_alerts": rows(StockAlert, or_(StockAlert.user_id == user.id, StockAlert.email == user.email)),
        "newsletter": [
            {k: v for k, v in r.items() if k != "token"} for r in rows(NewsletterSubscriber, NewsletterSubscriber.email == user.email)
        ],
        "analytics_events": rows(AnalyticsEvent, AnalyticsEvent.user_id == user.id),
    }
    body = jsonable_encoder(data)
    return Response(
        content=json.dumps(body, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="maru-my-data.json"'},
    )


@router.post("/erase", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(rate_limit("privacy_erase", 5, 3600))])
def erase_my_account(
    payload: EraseRequest, user: User = Depends(get_current_user_required), db: Session = Depends(get_db)
) -> Response:
    if payload.confirm != "DELETE":
        raise HTTPException(status_code=400, detail='Type DELETE to confirm')
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=403, detail="Incorrect password")
    if user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Staff accounts are removed by a super admin")

    unsettled = db.execute(
        select(Order.order_number).where(Order.user_id == user.id, Order.status.not_in(_SETTLED))
    ).scalars().all()
    if unsettled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You have orders in progress ({', '.join(unsettled)}). Erase your account after they are completed or cancelled.",
        )

    old_email = user.email
    try:
        for model in (Address, WishlistItem, TrustedDevice, LoginDeviceCode, PasswordResetToken, EmailVerificationToken, AdminLoginCode, Review):
            db.execute(delete(model).where(model.user_id == user.id))
        db.execute(delete(StockAlert).where(or_(StockAlert.user_id == user.id, StockAlert.email == old_email)))
        db.execute(delete(NewsletterSubscriber).where(NewsletterSubscriber.email == old_email))
        db.execute(update(AnalyticsEvent).where(AnalyticsEvent.user_id == user.id).values(user_id=None))

        # Open (never-ordered) carts go away; a cart that became an order stays
        # because the order references it, but loses its owner.
        open_cart_ids = db.execute(select(Cart.id).where(Cart.user_id == user.id, Cart.converted_at.is_(None))).scalars().all()
        if open_cart_ids:
            db.execute(delete(CartItem).where(CartItem.cart_id.in_(open_cart_ids)))
            db.execute(delete(Cart).where(Cart.id.in_(open_cart_ids)))
        db.execute(update(Cart).where(Cart.user_id == user.id).values(user_id=None, is_active=False))

        user.email = f"deleted-{user.id}@deleted.invalid"
        user.password_hash = hash_password(token_urlsafe(32))
        user.first_name = user.last_name = user.phone = None
        user.is_active = False
        user.email_verified = False
        user.mfa_secret = None
        user.mfa_enabled = False
        log_audit(db, None, "account_erased", "user", user.id, None, {"self_service": True})
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to erase account") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
