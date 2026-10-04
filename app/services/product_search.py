"""Catalogue search, in the database (PRD ТЗ№1 §47, with the 100 000-product target of §46).

A product matches when every word of the query is found in its name (or its translated name for the visitor's
language), its SKU codes, shape, purpose, category name, or equals its volume ("1000" / "1000ml"). Results are
ranked: exact SKU code, then names that start with the query, then names that contain it, then the rest.
When nothing matches, a typo-tolerant pass looks for names that are within one or two edits of the words typed
(the list of names is cached, so the cost is paid once per few minutes, not per search).
"""

import re
from typing import Optional

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from app.core import cache
from app.config import settings
from app.models import Category, Product, ProductVariant, SKU
from app.models.product_translation import ProductTranslation

MAX_QUERY_LENGTH = 80
_WORD = re.compile(r"[^\W_]+", re.UNICODE)


def tokens(query: str) -> list:
    return [w.lower() for w in _WORD.findall(query[:MAX_QUERY_LENGTH])][:6]


def _volume_of(token: str) -> Optional[int]:
    m = re.fullmatch(r"(\d{2,4})(?:ml|мл|ml\.)?", token)
    return int(m.group(1)) if m else None


def _like(column, token: str):
    escaped = token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return func.lower(column).like(f"%{escaped}%", escape="\\")


def text_filter(words: list, lang: Optional[str]) -> list:
    """WHERE conditions that make a product match every word. The query must also join Category and, when
    `lang` is given, an outer join of ProductTranslation for that language (see find_product_ids)."""
    conds = []
    for word in words:
        options = [
            _like(Product.name, word), _like(SKU.sku_code, word), _like(Product.shape, word),
            _like(Product.purpose, word), _like(Category.name, word),
        ]
        if lang:
            options.append(_like(ProductTranslation.name, word))
        volume = _volume_of(word)
        if volume is not None:
            options.append(Product.volume_ml == volume)
        conds.append(or_(*options))
    return conds


def relevance(words: list):
    """Sort expression: exact SKU code, then name starts with the query, then name contains it, then the rest."""
    full = " ".join(words)
    name_expr = func.lower(Product.name)
    return func.min(
        case(
            (func.lower(SKU.sku_code) == full.replace(" ", ""), 0),
            (name_expr.like(_prefix(full)), 1),
            (name_expr.like(f"%{full}%"), 2),
            else_=3,
        )
    )


def fuzzy_product_ids(db: Session, words: list, lang: Optional[str], base_conditions: list) -> list:
    """Ids of products whose names are within a couple of typos of the words typed, closest first."""
    return _fuzzy_ids(db, words, lang, base_conditions, 1, None)[0]


def search_ids(db: Session, query: str, lang: Optional[str], base_conditions: list, page: int, limit: Optional[int]) -> tuple:
    """Returns (product ids of the page, total matches). `base_conditions` are the usual "active variant and SKU"
    conditions of the catalogue."""
    words = tokens(query)
    if not words:
        return [], 0

    translation = None
    stmt = (
        select(Product.id.label("pid"))
        .select_from(Product)
        .join(Category, Category.id == Product.category_id)
        .join(ProductVariant, ProductVariant.product_id == Product.id)
        .join(SKU, SKU.variant_id == ProductVariant.id)
    )
    name_expr = func.lower(Product.name)
    if lang:
        translation = ProductTranslation
        stmt = stmt.outerjoin(ProductTranslation, and_(ProductTranslation.product_id == Product.id, ProductTranslation.locale == lang))
    conds = list(base_conditions)
    for word in words:
        options = [
            _like(Product.name, word), _like(SKU.sku_code, word), _like(Product.shape, word),
            _like(Product.purpose, word), _like(Category.name, word),
        ]
        if translation is not None:
            options.append(_like(ProductTranslation.name, word))
        volume = _volume_of(word)
        if volume is not None:
            options.append(Product.volume_ml == volume)
        conds.append(or_(*options))
    stmt = stmt.where(*conds).group_by(Product.id)

    full = " ".join(words)
    rank = func.min(
        case(
            (func.lower(SKU.sku_code) == full.replace(" ", ""), 0),
            (name_expr.like(_prefix(full)), 1),
            (name_expr.like(f"%{full}%"), 2),
            else_=3,
        )
    )
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    if total == 0:
        return _fuzzy_ids(db, words, lang, base_conditions, page, limit)
    paged = stmt.order_by(rank, Product.id)
    if limit is not None:
        paged = paged.limit(limit).offset((page - 1) * limit)
    return [row.pid for row in db.execute(paged)], total


def _prefix(text: str) -> str:
    return text.replace("%", "").replace("_", "") + "%"


# ---- typo tolerance ---------------------------------------------------------------------

def _edit_distance(a: str, b: str, cap: int) -> int:
    """Levenshtein distance, giving up (returning cap + 1) once it is certain to exceed `cap`."""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        if min(current) > cap:
            return cap + 1
        previous = current
    return previous[-1]


def _name_index(db: Session, lang: Optional[str], base_conditions: list) -> list:
    """[(product_id, [lowercase words of its names and sku codes])] for every sellable product, cached."""

    def load():
        rows = db.execute(
            select(Product.id, Product.name, Product.shape, Product.purpose)
            .join(ProductVariant, ProductVariant.product_id == Product.id)
            .join(SKU, SKU.variant_id == ProductVariant.id)
            .where(*base_conditions)
            .group_by(Product.id, Product.name, Product.shape, Product.purpose)
        ).all()
        names = {}
        if lang:
            names = dict(db.execute(select(ProductTranslation.product_id, ProductTranslation.name).where(ProductTranslation.locale == lang)).all())
        index = []
        for pid, name, shape, purpose in rows:
            words = set(_WORD.findall(f"{name} {names.get(pid, '')} {shape or ''} {purpose or ''}".lower()))
            index.append([pid, sorted(words)])
        return index

    return cache.get_or_set("catalog", f"names:{lang or ''}", settings.CACHE_TTL_SECONDS, load)


def _fuzzy_ids(db: Session, words: list, lang: Optional[str], base_conditions: list, page: int, limit: Optional[int]) -> tuple:
    scored = []
    for pid, product_words in _name_index(db, lang, base_conditions):
        total_distance = 0
        for w in words:
            cap = 1 if len(w) <= 4 else 2
            best = min((_edit_distance(w, pw, cap) for pw in product_words), default=cap + 1)
            if best > cap:
                total_distance = None
                break
            total_distance += best
        if total_distance is not None:
            scored.append((total_distance, pid))
    scored.sort()
    ids = [pid for _d, pid in scored]
    total = len(ids)
    if limit is not None:
        ids = ids[(page - 1) * limit: page * limit]
    return ids, total

