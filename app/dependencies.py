from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models.cart import Cart
from app.models.enums import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        return None

    return user


def get_current_user_required(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def require_role(*roles: UserRole):
    def dependency(user: User = Depends(get_current_user_required)) -> User:
        if user.role != UserRole.SUPER_ADMIN and user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        # Every admin-role endpoint additionally requires the /admin 2-step
        # email-code login (app/routers/auth.py's admin_login_request/
        # admin_login_verify) to have been completed recently — a plain
        # site login is not enough to reach the admin panel or its API.
        if user.admin_mfa_verified_until is None or user.admin_mfa_verified_until < datetime.now(timezone.utc).replace(tzinfo=None):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_verification_required")
        return user

    return dependency


def get_or_create_cart(
    response: Response,
    x_cart_token: Optional[str] = Header(default=None, alias="X-Cart-Token"),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Cart:
    """Resolve the caller's active cart. Authenticated users are matched by
    user_id; guests are matched by an X-Cart-Token header, minted on first use
    and echoed back so the client can persist and resend it (PRD section 10)."""
    try:
        if user is not None:
            cart = db.execute(
                select(Cart).where(Cart.user_id == user.id, Cart.is_active.is_(True))
            ).scalar_one_or_none()
            if cart is None:
                cart = Cart(user_id=user.id)
                db.add(cart)
                db.commit()
                db.refresh(cart)
            return cart

        cart = None
        if x_cart_token:
            cart = db.execute(
                select(Cart).where(Cart.token == x_cart_token, Cart.is_active.is_(True))
            ).scalar_one_or_none()

        if cart is None:
            cart = Cart(token=uuid4().hex)
            db.add(cart)
            db.commit()
            db.refresh(cart)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to resolve cart") from exc

    response.headers["X-Cart-Token"] = cart.token
    return cart
