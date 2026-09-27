from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category_translation import CategoryTranslation
from app.models.product_translation import ProductTranslation

# MVP languages (PRD section 15: ru/uz/en minimum). Adding a locale here is the
# only code change needed — storage is a plain string column, not an enum.
ALLOWED_LOCALES = ("ru", "uz", "en")


def get_category_translations(db: Session, category_ids: list[int], locale: str) -> dict[int, str]:
    if not category_ids:
        return {}
    rows = (
        db.execute(
            select(CategoryTranslation).where(
                CategoryTranslation.category_id.in_(category_ids), CategoryTranslation.locale == locale
            )
        )
        .scalars()
        .all()
    )
    return {row.category_id: row.name for row in rows}


def get_product_translation(db: Session, product_id: int, locale: str) -> ProductTranslation | None:
    return db.execute(
        select(ProductTranslation).where(
            ProductTranslation.product_id == product_id, ProductTranslation.locale == locale
        )
    ).scalar_one_or_none()


def get_product_translations(db: Session, product_ids: list[int], locale: str) -> dict[int, ProductTranslation]:
    if not product_ids:
        return {}
    rows = (
        db.execute(
            select(ProductTranslation).where(
                ProductTranslation.product_id.in_(product_ids), ProductTranslation.locale == locale
            )
        )
        .scalars()
        .all()
    )
    return {row.product_id: row for row in rows}
