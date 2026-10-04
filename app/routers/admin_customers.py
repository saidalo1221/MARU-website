from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.pagination import PageParams, page_params, paged
from app.database import get_db
from app.dependencies import require_role
from app.models.enums import CustomerType, OrderStatus, UserRole
from app.models.order import Order
from app.models.user import User
from app.schemas.user import UserOut
from app.services.audit import log_audit

# Customer accounts (PRD ТЗ№1 §33: users, B2B customers, distributors). Staff accounts are managed on the
# Administrators page, never here.
router = APIRouter(prefix="/admin/customers", tags=["admin-customers"])

_ROLES = (UserRole.SALES_MANAGER, UserRole.ACCOUNTANT)


class CustomerRow(UserOut):
    order_count: int = 0
    last_order_at: Optional[str] = None


class CustomerUpdate(BaseModel):
    customer_type: Optional[CustomerType] = None
    is_active: Optional[bool] = None


@router.get("/", response_model=list[CustomerRow])
def list_customers(
    response: Response,
    q: Optional[str] = None,
    customer_type: Optional[CustomerType] = None,
    params: PageParams = Depends(page_params),
    user: User = Depends(require_role(*_ROLES)),
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = select(User).where(User.role == UserRole.CUSTOMER).order_by(User.id.desc())
    if q:
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(User.email).like(like), func.lower(func.coalesce(User.first_name, "")).like(like),
                              func.lower(func.coalesce(User.last_name, "")).like(like), func.coalesce(User.phone, "").like(like)))
    if customer_type is not None:
        stmt = stmt.where(User.customer_type == customer_type)
    users = paged(db, response, stmt, stmt, params)

    ids = [u.id for u in users]
    stats = {}
    if ids:
        for uid, n, last in db.execute(
            select(Order.user_id, func.count(Order.id), func.max(Order.created_at))
            .where(Order.user_id.in_(ids), Order.status.notin_((OrderStatus.CANCELLED, OrderStatus.PAYMENT_FAILED)))
            .group_by(Order.user_id)
        ):
            stats[uid] = (n, last.isoformat() if last else None)
    out = []
    for u in users:
        row = CustomerRow.model_validate(u).model_dump()
        row["order_count"], row["last_order_at"] = stats.get(u.id, (0, None))
        out.append(row)
    return out


@router.patch("/{user_id}", response_model=UserOut)
def update_customer(
    user_id: int,
    payload: CustomerUpdate,
    user: User = Depends(require_role(UserRole.SALES_MANAGER)),
    db: Session = Depends(get_db),
) -> User:
    target = db.get(User, user_id)
    if target is None or target.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=404, detail="Customer not found")
    changes = payload.model_dump(exclude_unset=True)
    log_audit(
        db, user, "customer_update", "user", target.id,
        {k: getattr(getattr(target, k), "value", getattr(target, k)) for k in changes},
        {k: getattr(v, "value", v) for k, v in changes.items()},
    )
    for field, value in changes.items():
        setattr(target, field, value)
    db.commit()
    db.refresh(target)
    return target
