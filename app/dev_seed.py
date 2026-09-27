"""Seeds a minimal demo catalog for local development/manual testing —
categories, products, variants, SKUs, a warehouse with stock, shipping
rates, exchange rates, and RU/UZ product translations. Not used in
production and not used by the test suite (see tests/conftest.py, which
builds its own isolated per-test database).

Usage (against a throwaway local SQLite file, not the real MariaDB):

    DATABASE_URL=sqlite:///dev.db python -m app.dev_seed
    uvicorn app.main:app --reload      # in another terminal

Safe to run once per fresh database; re-running against an already-seeded
one will hit unique-constraint conflicts (slugs, SKU codes, currencies).
Delete the SQLite file to start over.
"""

import os

from sqlalchemy import BigInteger
from sqlalchemy.ext.compiler import compiles

# SQLite only treats a bare INTEGER PRIMARY KEY as an autoincrement rowid
# alias; BigInteger PKs need this to insert without an explicit id.
# MariaDB has no such quirk, so this only takes effect under sqlite.
if "sqlite" in os.environ.get("DATABASE_URL", ""):

    @compiles(BigInteger, "sqlite")
    def _bigint_as_integer(type_, compiler, **kw):
        return "INTEGER"


import app.models  # noqa: F401  (registers every model on Base.metadata)
from app.database import Base, SessionLocal, engine
from app.models.category import Category
from app.models.exchange_rate import ExchangeRate
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_translation import ProductTranslation
from app.models.product_variant import ProductVariant
from app.models.shipping_rate import ShippingRate
from app.models.sku import SKU
from app.models.warehouse import Warehouse

CATEGORIES_AND_PRODUCTS = [
    (
        "Food Containers",
        "food-containers",
        [
            (
                "MARU Round Container",
                "maru-round-container",
                350,
                [("Clear", "clear", "SKU-350-CLR", 3.50, 500)],
                {
                    "ru": ("Круглый контейнер MARU", "Пищевой контейнер объемом 350 мл из полипропилена."),
                    "uz": ("MARU dumaloq idishi", "350 ml hajmli polipropilendan yasalgan oziq-ovqat idishi."),
                },
            ),
            (
                "MARU Rectangular Container",
                "maru-rect-container",
                1000,
                [("Clear", "clear", "SKU-1000-CLR", 6.90, 200)],
                {
                    "ru": ("Прямоугольный контейнер MARU", "Пищевой контейнер объемом 1000 мл из полипропилена."),
                    "uz": ("MARU to'rtburchak idishi", "1000 ml hajmli polipropilendan yasalgan oziq-ovqat idishi."),
                },
            ),
        ],
    ),
]


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    warehouse = Warehouse(name="Main Warehouse", country="Uzbekistan", priority=1)
    db.add(warehouse)
    db.flush()

    # "*" is the wildcard fallback tier; a concrete country is also needed
    # since /shipping/countries deliberately excludes "*" from the storefront's
    # country picker.
    for country in ("*", "Uzbekistan"):
        db.add(ShippingRate(country=country, delivery_method="Courier", base_fee=5, per_kg_fee=1))
        db.add(ShippingRate(country=country, delivery_method="Pickup", base_fee=0, per_kg_fee=0))

    db.add_all(
        [
            ExchangeRate(currency="UZS", units_per_usd=12500),
            ExchangeRate(currency="EUR", units_per_usd="0.92"),
            ExchangeRate(currency="KZT", units_per_usd=450),
            ExchangeRate(currency="AED", units_per_usd="3.67"),
        ]
    )

    for cat_name, cat_slug, products in CATEGORIES_AND_PRODUCTS:
        category = Category(name=cat_name, slug=cat_slug)
        db.add(category)
        db.flush()
        for prod_name, prod_slug, volume_ml, variants, translations in products:
            product = Product(category_id=category.id, name=prod_name, slug=prod_slug, volume_ml=volume_ml)
            db.add(product)
            db.flush()
            for locale, (name, description) in translations.items():
                db.add(ProductTranslation(product_id=product.id, locale=locale, name=name, description=description))
            for variant_name, color, sku_code, price, stock in variants:
                variant = ProductVariant(product_id=product.id, name=variant_name, color=color)
                db.add(variant)
                db.flush()
                sku = SKU(
                    variant_id=variant.id, sku_code=sku_code, retail_price=price, currency="USD", unit_weight_g=50
                )
                db.add(sku)
                db.flush()
                db.add(Inventory(sku_id=sku.id, warehouse_id=warehouse.id, stock=stock, reserved=0))

    db.commit()
    print("Seeded dev catalog.")


if __name__ == "__main__":
    run()
