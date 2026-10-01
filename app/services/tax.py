from typing import Optional
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.tax_rule import ANY, TaxRule
from app.services.currency import get_rate_to_usd


def _find_rule(
    db: Session, country: str, region: Optional[str], customer_type: str, tax_type: str, taxable_usd: Decimal
) -> Optional[TaxRule]:
    """Most-specific match first: country, then region, then customer type
    (same wildcard fallback shape as app/services/shipping.py._find_rate()).
    Among rules for the same key, the highest min_order_amount the taxable
    amount still reaches wins."""
    region_key = (region or "").strip().lower()
    regions = [region_key, ANY] if region_key else [ANY]
    for country_key in (country, ANY):
        for rk in regions:
            for customer_type_key in (customer_type, ANY):
                rule = db.execute(
                    select(TaxRule)
                    .where(
                        TaxRule.country == country_key,
                        func.lower(TaxRule.region) == rk,
                        TaxRule.customer_type == customer_type_key,
                        TaxRule.tax_type == tax_type,
                        TaxRule.is_active.is_(True),
                        TaxRule.min_order_amount <= taxable_usd,
                    )
                    .order_by(TaxRule.min_order_amount.desc())
                    .limit(1)
                ).scalar_one_or_none()
                if rule is not None:
                    return rule
    return None


def calculate_tax(
    db: Session,
    country: str,
    customer_type: str,
    taxable_amount: Decimal,
    tax_type: str = "vat",
    region: Optional[str] = None,
    currency: str = "USD",
) -> Decimal:
    """Unlike shipping (app/services/shipping.py), an unconfigured
    country/customer_type is not an error here - it means "no tax applies in
    this jurisdiction yet", which is a normal, common state (PRD gives no
    "must be configured" acceptance criterion for tax the way it does for
    shipping). Returns 0 rather than raising. `currency` is the currency of
    taxable_amount; it is only used to compare against a rule's USD
    min_order_amount."""
    if taxable_amount <= 0:
        return Decimal("0.00")
    taxable_usd = taxable_amount / get_rate_to_usd(db, currency)
    rule = _find_rule(db, country, region, customer_type, tax_type, taxable_usd)
    if rule is None:
        return Decimal("0.00")
    tax = taxable_amount * (rule.rate / Decimal("100"))
    return tax.quantize(Decimal("0.01"))
