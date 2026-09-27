from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.exchange_rate import ExchangeRate
from app.models.user import User
from app.schemas.exchange_rate import ExchangeRateCreate, ExchangeRateOut, ExchangeRateUpdate

# Gated to Product Manager, who PRD section 34 assigns "Каталог и цены" (catalog and pricing).
router = APIRouter(prefix="/admin/exchange-rates", tags=["admin-exchange-rates"])


@router.get("/", response_model=list[ExchangeRateOut])
def list_exchange_rates(
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> list[ExchangeRate]:
    try:
        rates = db.execute(select(ExchangeRate).order_by(ExchangeRate.currency)).scalars().all()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch exchange rates") from exc

    return list(rates)


@router.post("/", response_model=ExchangeRateOut, status_code=status.HTTP_201_CREATED)
def create_exchange_rate(
    payload: ExchangeRateCreate,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> ExchangeRate:
    rate = ExchangeRate(**payload.model_dump())
    db.add(rate)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="A rate for this currency already exists"
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create exchange rate") from exc

    db.refresh(rate)
    return rate


@router.patch("/{rate_id}", response_model=ExchangeRateOut)
def update_exchange_rate(
    rate_id: int,
    payload: ExchangeRateUpdate,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> ExchangeRate:
    try:
        rate = db.get(ExchangeRate, rate_id)
        if rate is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange rate not found")

        rate.units_per_usd = payload.units_per_usd
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update exchange rate") from exc

    db.refresh(rate)
    return rate
