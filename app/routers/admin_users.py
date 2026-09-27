from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import AdminPromoteRequest, UserOut

router = APIRouter(prefix="/admin/users", tags=["admin-users"])

_ANY_ADMIN_ROLE = (
    UserRole.PRODUCT_MANAGER,
    UserRole.SALES_MANAGER,
    UserRole.WAREHOUSE_MANAGER,
    UserRole.ACCOUNTANT,
    UserRole.MARKETING_MANAGER,
)


@router.get("/session")
def check_admin_session(user: User = Depends(require_role(*_ANY_ADMIN_ROLE))) -> dict:
    """Lightweight probe the frontend calls to check whether the current
    account has completed the /admin 2-step email login — reaching this
    endpoint's body at all already proves it (require_role() raises before
    getting here otherwise)."""
    return {"detail": "ok"}


@router.get("/admins", response_model=list[UserOut])
def list_admins(
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
) -> list[User]:
    return list(db.execute(select(User).where(User.role != UserRole.CUSTOMER).order_by(User.email)).scalars().all())


@router.post("/promote", response_model=UserOut)
def promote_to_admin(
    payload: AdminPromoteRequest,
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
) -> User:
    if payload.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use the demote endpoint instead")

    target = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account registered with that email")

    try:
        target.role = payload.role
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update role") from exc
    db.refresh(target)
    return target


@router.post("/{user_id}/demote", response_model=UserOut)
def demote_to_customer(
    user_id: int,
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
) -> User:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot demote yourself")

    try:
        target.role = UserRole.CUSTOMER
        target.admin_mfa_verified_until = None
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update role") from exc
    db.refresh(target)
    return target
