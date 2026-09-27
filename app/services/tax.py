from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tax_rule import ANY, TaxRule


def _find_rule(db: Session, country: str, customer_type: str, tax_type: str) -> TaxRule | None:
    """Most-specific match first, same fallback shape as
    app/services/shipping.py._find_rate()."""
    candidates = [
        (country, customer_type),
        (country, ANY),
        (ANY, customer_type),
        (ANY, ANY),
    ]
    for country_key, customer_type_key in candidates:
        rule = db.execute(
            select(TaxRule).where(
                TaxRule.country == country_key,
                TaxRule.customer_type == customer_type_key,
                TaxRule.tax_type == tax_type,
                TaxRule.is_active.is_(True),
            )
        ).scalar_one_or_none()
        if rule is not None:
            return rule
    return None


def calculate_tax(db: Session, country: str, customer_type: str, taxable_amount: Decimal, tax_type: str = "vat") -> Decimal:
    """Unlike shipping (app/services/shipping.py), an unconfigured
    country/customer_type is not an error here — it means "no tax applies in
    this jurisdiction yet", which is a normal, common state (PRD gives no
    "must be configured" acceptance criterion for tax the way it does for
    shipping). Returns 0 rather than raising."""
    rule = _find_rule(db, country, customer_type, tax_type)
    if rule is None or taxable_amount <= 0:
        return Decimal("0.00")
    tax = taxable_amount * (rule.rate / Decimal("100"))
    return tax.quantize(Decimal("0.01"))
