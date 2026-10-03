"""Which products are sold in which market (PRD ТЗ№1 §16: "available assortment" per market).

A product can be limited to some countries (`sold_in_countries`: only there) and/or hidden in some
(`hidden_in_countries`: everywhere but there). With neither set it is sold everywhere, which is how every
product starts. Country names are compared without regard to case; they are the same names customers pick in the
delivery-country selector. When the visitor has not chosen a country nothing is filtered.
"""

from typing import Iterable, Optional

from sqlalchemy import and_, func, not_, or_

from app.models import Product


def _norm(country: Optional[str]) -> str:
    return (country or "").strip().lower()


def _needle(country: str) -> str:
    # The columns hold JSON text like ["uzbekistan","kazakhstan"]; match the quoted, lower-cased name.
    safe = country.replace("\\", "").replace('"', "").replace("%", "").replace("_", "")
    return f'%"{safe}"%'


def condition(country: Optional[str]):
    """SQL condition for "this product may be shown to a visitor in `country`"; None when no country is known."""
    c = _norm(country)
    if not c:
        return None
    needle = _needle(c)
    return and_(
        or_(Product.sold_in_countries.is_(None), func.lower(Product.sold_in_countries).like(needle)),
        or_(Product.hidden_in_countries.is_(None), not_(func.lower(Product.hidden_in_countries).like(needle))),
    )


def is_available(product, country: Optional[str]) -> bool:
    c = _norm(country)
    if not c:
        return True
    sold: Optional[Iterable[str]] = product.sold_in_countries
    hidden: Optional[Iterable[str]] = product.hidden_in_countries
    if sold and c not in {_norm(x) for x in sold}:
        return False
    if hidden and c in {_norm(x) for x in hidden}:
        return False
    return True
