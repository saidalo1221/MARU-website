from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.promo_code import PromoCode
from app.models.user import User
from app.services.audit import audit_create, audit_update, log_audit
from app.schemas.promo_code import PromoCodeCreate, PromoCodeOut, PromoCodeUpdate

router = APIRouter(prefix="/admin/promo-codes", tags=["admin-promo-codes"])


@router.get("/", response_model=list[PromoCodeOut])
def list_promo_codes(
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> list[PromoCode]:
    try:
        codes = db.execute(select(PromoCode).order_by(PromoCode.id.desc())).scalars().all()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch promo codes") from exc

    return list(codes)


@router.post("/", response_model=PromoCodeOut, status_code=status.HTTP_201_CREATED)
def create_promo_code(
    payload: PromoCodeCreate,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> PromoCode:
    code = PromoCode(**payload.model_dump())
    db.add(code)
    try:
        audit_create(db, user, "promo_create", "promo_code", code, payload.model_dump())
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promo code already exists") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create promo code") from exc

    db.refresh(code)
    return code


@router.get("/{promo_id}", response_model=PromoCodeOut)
def get_promo_code(
    promo_id: int,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> PromoCode:
    try:
        code = db.get(PromoCode, promo_id)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch promo code") from exc

    if code is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo code not found")

    return code


@router.patch("/{promo_id}", response_model=PromoCodeOut)
def update_promo_code(
    promo_id: int,
    payload: PromoCodeUpdate,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> PromoCode:
    try:
        code = db.get(PromoCode, promo_id)
        if code is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo code not found")

        changes = payload.model_dump(exclude_unset=True)
        audit_update(db, user, "promo_update", "promo_code", code, changes)
        for field, value in changes.items():
            setattr(code, field, value)

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update promo code") from exc

    db.refresh(code)
    return code
