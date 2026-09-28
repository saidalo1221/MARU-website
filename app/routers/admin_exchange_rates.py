from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.exchange_rate import ExchangeRate
from app.models.user import User
from app.schemas.exchange_rate import CurrencyOption, ExchangeRateCreate, ExchangeRateOut, ExchangeRateUpdate
from app.services.fx_provider import FxProviderError, fetch_rate_for_currency, fetch_supported_currencies, sync_exchange_rates

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


@router.get("/available-currencies", response_model=list[CurrencyOption])
def list_available_currencies(
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
) -> list[dict[str, str]]:
    """Backs the searchable currency picker on "Add Currency" — every
    code/name pair the FX provider supports, not just ones already added."""
    try:
        return fetch_supported_currencies()
    except FxProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/", response_model=ExchangeRateOut, status_code=status.HTTP_201_CREATED)
def create_exchange_rate(
    payload: ExchangeRateCreate,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> ExchangeRate:
    units_per_usd = payload.units_per_usd
    if units_per_usd is None:
        try:
            units_per_usd = fetch_rate_for_currency(payload.currency)
        except FxProviderError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    rate = ExchangeRate(currency=payload.currency, units_per_usd=units_per_usd)
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


@router.post("/sync", response_model=list[ExchangeRateOut])
def sync_rates_from_provider(
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> list[ExchangeRate]:
    """On-demand refresh from the live FX feed (app/services/fx_provider.py)
    — the same one app/tasks/sync_exchange_rates.py runs on a schedule.
    Safe to call manually: it's a single request against the provider's
    free tier (1,500/month), not a loop."""
    try:
        sync_exchange_rates(db)
    except FxProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    rates = db.execute(select(ExchangeRate).order_by(ExchangeRate.currency)).scalars().all()
    return list(rates)


@router.delete("/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exchange_rate(
    rate_id: int,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> None:
    rate = db.get(ExchangeRate, rate_id)
    if rate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange rate not found")
    try:
        db.delete(rate)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete exchange rate") from exc


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
