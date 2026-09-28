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
from app.models.blog_category import BlogCategory
from app.models.blog_post import BlogPost
from app.models.blog_post_translation import BlogPostTranslation
from app.models.site_settings import SiteSettings
from app.models.about_section import AboutSection
from app.models.about_section_translation import AboutSectionTranslation
from datetime import datetime, timedelta

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

# (category_name, category_slug, [(slug, title, excerpt, content, author_name,
# days_ago_published, {locale: (title, excerpt, content)})])
BLOG_CATEGORIES_AND_POSTS = [
    (
        "Sustainability",
        "sustainability",
        [
            (
                "how-maru-reduces-plastic-waste",
                "How MARU Reduces Plastic Waste",
                "A look at the recycling programs and material choices behind our containers.",
                "MARU containers are made from food-grade polypropylene chosen for "
                "durability and recyclability. This article covers our take-back "
                "program and how customers can recycle used containers.",
                "MARU Team",
                2,
                {
                    "ru": (
                        "Как MARU сокращает пластиковые отходы",
                        "Взгляд на программы переработки и выбор материалов для наших контейнеров.",
                        "Контейнеры MARU изготовлены из пищевого полипропилена, выбранного "
                        "за долговечность и перерабатываемость. В этой статье рассказывается "
                        "о нашей программе приема тары и о том, как клиенты могут "
                        "перерабатывать использованные контейнеры.",
                    ),
                    "uz": (
                        "MARU plastik chiqindilarni qanday kamaytiradi",
                        "Idishlarimiz uchun qayta ishlash dasturlari va material tanlovlariga nazar.",
                        "MARU idishlari chidamliligi va qayta ishlanishi uchun tanlangan "
                        "oziq-ovqat toifasidagi polipropilendan tayyorlanadi. Ushbu maqolada "
                        "bizning qabul qilish dasturimiz va mijozlar ishlatilgan idishlarni "
                        "qanday qayta ishlashi mumkinligi haqida so'z boradi.",
                    ),
                },
            ),
        ],
    ),
    (
        "Product Care",
        "product-care",
        [
            (
                "keeping-your-containers-fresh",
                "Keeping Your Containers Fresh",
                "Simple cleaning and storage tips to extend the life of your MARU containers.",
                "Hand-wash with mild detergent, avoid abrasive scrubbers, and let "
                "lids air-dry to prevent odor buildup. Our containers are also "
                "top-rack dishwasher safe.",
                "MARU Team",
                7,
                {
                    "ru": (
                        "Как сохранить контейнеры свежими",
                        "Простые советы по уходу и хранению для продления срока службы контейнеров MARU.",
                        "Мойте вручную мягким моющим средством, избегайте абразивных губок "
                        "и дайте крышкам высохнуть на воздухе, чтобы избежать появления "
                        "запаха. Наши контейнеры также можно мыть в посудомоечной машине "
                        "на верхней полке.",
                    ),
                    "uz": (
                        "Idishlaringizni yangi holatda saqlash",
                        "MARU idishlaringiz umrini uzaytirish uchun oddiy tozalash va saqlash maslahatlari.",
                        "Yumshoq yuvish vositasi bilan qo'lda yuving, qattiq g'ovaklardan "
                        "saqlaning va qopqoqlarni hidning to'planishini oldini olish uchun "
                        "havoda quriting. Idishlarimiz idish yuvish mashinasining yuqori "
                        "javonida yuvishga ham xavfsiz.",
                    ),
                },
            ),
        ],
    ),
]

# (title, body, {locale: (title, body)}) — the free-form About Us sections
# (app/models/about_section.py), seeded with what used to be the hardcoded
# History/Company/Production/Equipment/Quality/Products/Markets copy.
ABOUT_SECTIONS = [
    (
        "History",
        "MARU was founded to bring reliable, food-safe plastic packaging to local and regional markets.",
        {
            "ru": ("История", "MARU была основана, чтобы предложить надёжную, безопасную для пищевых продуктов упаковку на местном и региональном рынках."),
            "uz": ("Tarix", "MARU mahalliy va mintaqaviy bozorlarga ishonchli, oziq-ovqat uchun xavfsiz plastik qadoqlashni yetkazib berish maqsadida tashkil etilgan."),
        },
    ),
    (
        "Company",
        "We manufacture, package, and ship polypropylene food containers directly to businesses and individuals.",
        {
            "ru": ("Компания", "Мы производим, упаковываем и отправляем полипропиленовые контейнеры напрямую компаниям и частным клиентам."),
            "uz": ("Kompaniya", "Biz polipropilen oziq-ovqat idishlarini ishlab chiqaramiz, qadoqlaymiz va to'g'ridan-to'g'ri kompaniyalar hamda yakka tartibdagi mijozlarga yetkazamiz."),
        },
    ),
    (
        "Production",
        "Our containers are produced in-house, from raw polypropylene to the finished, packaged product.",
        {
            "ru": ("Производство", "Наши контейнеры производятся собственными силами — от сырого полипропилена до готовой упакованной продукции."),
            "uz": ("Ishlab chiqarish", "Idishlarimiz xom polipropilendan tayyor, qadoqlangan mahsulotgacha o'zimizda ishlab chiqariladi."),
        },
    ),
    (
        "Equipment",
        "We invest in modern injection-molding equipment to keep quality and output consistent.",
        {
            "ru": ("Оборудование", "Мы инвестируем в современное оборудование для литья под давлением, чтобы поддерживать стабильное качество и объёмы."),
            "uz": ("Uskunalar", "Sifat va hajmni barqaror saqlash uchun zamonaviy quyma uskunalarga sarmoya kiritamiz."),
        },
    ),
    (
        "Quality",
        "Every batch is checked for food-safety compliance before it reaches a customer.",
        {
            "ru": ("Качество", "Каждая партия проверяется на соответствие требованиям пищевой безопасности перед отправкой клиенту."),
            "uz": ("Sifat", "Har bir partiya mijozga yetib borishidan oldin oziq-ovqat xavfsizligi talablariga muvofiqligi tekshiriladi."),
        },
    ),
    (
        "Products",
        "Polypropylene containers from 350 ml to 1900 ml, in various shapes and colors.",
        {
            "ru": ("Продукция", "Полипропиленовые контейнеры от 350 до 1900 мл различных форм и цветов."),
            "uz": ("Mahsulotlar", "350 ml dan 1900 ml gacha turli shakl va rangdagi polipropilen idishlar."),
        },
    ),
    (
        "Markets",
        "Serving retail, wholesale, and distributor customers in Uzbekistan and beyond.",
        {
            "ru": ("Рынки", "Обслуживаем розничных, оптовых клиентов и дистрибьюторов в Узбекистане и за его пределами."),
            "uz": ("Bozorlar", "O'zbekiston va undan tashqarida chakana, ulgurji va distribyutor mijozlarga xizmat ko'rsatamiz."),
        },
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

    for cat_name, cat_slug, posts in BLOG_CATEGORIES_AND_POSTS:
        blog_category = BlogCategory(name=cat_name, slug=cat_slug)
        db.add(blog_category)
        db.flush()
        for post_slug, title, excerpt, content, author_name, days_ago, translations in posts:
            post = BlogPost(
                category_id=blog_category.id,
                slug=post_slug,
                title=title,
                excerpt=excerpt,
                content=content,
                author_name=author_name,
                is_published=True,
                published_at=datetime.utcnow() - timedelta(days=days_ago),
            )
            db.add(post)
            db.flush()
            for locale, (t_title, t_excerpt, t_content) in translations.items():
                db.add(
                    BlogPostTranslation(
                        post_id=post.id, locale=locale, title=t_title, excerpt=t_excerpt, content=t_content
                    )
                )

    db.add(
        SiteSettings(
            id=1,
            phone="+998 71 200 00 00",
            email="info@maruplast.uz",
            address="Tashkent, Uzbekistan",
            latitude=41.2995,
            longitude=69.2401,
            about_title="About MARU",
            about_body="We manufacture polypropylene food containers in-house.",
        )
    )

    for order, (title, body, translations) in enumerate(ABOUT_SECTIONS, start=1):
        section = AboutSection(title=title, body=body, sort_order=order)
        db.add(section)
        db.flush()
        for locale, (t_title, t_body) in translations.items():
            db.add(AboutSectionTranslation(section_id=section.id, locale=locale, title=t_title, body=t_body))

    db.commit()
    print("Seeded dev catalog.")


if __name__ == "__main__":
    run()
