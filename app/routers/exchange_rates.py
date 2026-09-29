from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.models.exchange_rate import ExchangeRate
from app.schemas.exchange_rate import ExchangeRateOut

# Public (any authenticated account, no admin role) read-only mirror of
# /admin/exchange-rates — the admin panel's individual sections are gated by
# different roles (PRODUCT_MANAGER for products, SALES_MANAGER for orders,
# etc.), but every section needs the same rate table to convert displayed
# money into the header's selected currency, so this can't be role-gated to
# just one of them. The rates themselves aren't sensitive — customers already
# get their effect via /products?currency= and /cart/currency.
router = APIRouter(prefix="/exchange-rates", tags=["exchange-rates"], dependencies=[Depends(rate_limit("exchange_rates", 120, 60))])


@router.get("/", response_model=list[ExchangeRateOut])
def list_exchange_rates_public(db: Session = Depends(get_db)) -> list[ExchangeRate]:
    return list(db.execute(select(ExchangeRate).order_by(ExchangeRate.currency)).scalars().all())
