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
from app.models.page_section import PageSection
from app.models.page_section_translation import PageSectionTranslation
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

# (page, title, body, {locale: (title, body)}) — free-form content sections
# for the Delivery/Payment/Returns/FAQ/Contact pages (app/models/page_section.py),
# seeded with what used to be the hardcoded copy in frontend/src/i18n/translations.js.
# FAQ Q&A pairs are seeded in English, Russian and Uzbek.
PAGE_SECTIONS = [
    (
        "delivery", "Uzbekistan",
        "Domestic delivery methods available at checkout:",
        {
            "ru": ("Узбекистан", "Способы доставки по стране, доступные при оформлении заказа:"),
            "uz": ("O'zbekiston", "Buyurtma rasmiylashtirishda mavjud bo'lgan mamlakat ichidagi yetkazib berish usullari:"),
        },
    ),
    (
        "delivery", "International Delivery",
        "We currently ship to the following countries:",
        {
            "ru": ("Международная доставка", "В настоящее время мы доставляем в следующие страны:"),
            "uz": ("Xalqaro yetkazib berish", "Hozirda quyidagi davlatlarga yetkazib beramiz:"),
        },
    ),
    (
        "delivery", "Tracking",
        "You can check your order's status anytime from your Orders page.",
        {
            "ru": ("Отслеживание", "Вы можете проверить статус заказа в любое время на странице «Заказы»."),
            "uz": ("Kuzatish", "Buyurtmangiz holatini istalgan vaqtda «Buyurtmalar» sahifasidan tekshirishingiz mumkin."),
        },
    ),
    (
        "delivery", "Restrictions",
        "Some delivery methods may not be available for all order sizes or destinations — the checkout page always shows what's actually available for your address.",
        {
            "ru": ("Ограничения", "Некоторые способы доставки могут быть недоступны для определённых объёмов заказа или адресов — страница оформления заказа всегда показывает реально доступные варианты для вашего адреса."),
            "uz": ("Cheklovlar", "Ba'zi yetkazib berish usullari barcha buyurtma hajmlari yoki manzillar uchun mavjud bo'lmasligi mumkin — buyurtma rasmiylashtirish sahifasi doim manzilingiz uchun haqiqatda mavjud variantlarni ko'rsatadi."),
        },
    ),
    (
        "payment", "Note",
        "Only methods available for your order are shown at checkout.",
        {
            "ru": ("Примечание", "При оформлении заказа показываются только способы, доступные для вашего заказа."),
            "uz": ("Eslatma", "Buyurtma rasmiylashtirishda faqat buyurtmangiz uchun mavjud usullar ko'rsatiladi."),
        },
    ),
    (
        "returns", "Conditions",
        "Items must be unused, in original packaging, and reported within the return window below.",
        {
            "ru": ("Условия", "Товар должен быть неиспользованным, в оригинальной упаковке, о возврате нужно заявить в указанный ниже срок."),
            "uz": ("Shartlar", "Mahsulot ishlatilmagan, original qadoqda bo'lishi va quyidagi muddatda xabar qilinishi kerak."),
        },
    ),
    (
        "returns", "Timeframe",
        "Returns must be requested within 14 days of delivery.",
        {
            "ru": ("Сроки", "Запрос на возврат нужно подать в течение 14 дней с момента доставки."),
            "uz": ("Muddat", "Qaytarish so'rovi yetkazib berilgan kundan 14 kun ichida berilishi kerak."),
        },
    ),
    (
        "returns", "Procedure",
        "Contact us with your order number and reason for return; we'll confirm the next steps by email.",
        {
            "ru": ("Процедура", "Свяжитесь с нами, указав номер заказа и причину возврата; мы подтвердим дальнейшие шаги по эл. почте."),
            "uz": ("Tartib", "Buyurtma raqamingiz va qaytarish sababini ko'rsatib biz bilan bog'laning; keyingi qadamlarni elektron pochta orqali tasdiqlaymiz."),
        },
    ),
    (
        "returns", "Exceptions",
        "Custom or bulk wholesale orders may not be eligible for return — this is confirmed at order time.",
        {
            "ru": ("Исключения", "Индивидуальные или крупные оптовые заказы могут не подлежать возврату — это уточняется при оформлении заказа."),
            "uz": ("Istisnolar", "Individual yoki katta ulgurji buyurtmalar qaytarilmasligi mumkin — bu buyurtma vaqtida aniqlanadi."),
        },
    ),
    (
        "contact", "Business Inquiries",
        "For business or wholesale inquiries, use the form and select the matching request type on the Request a Quote page.",
        {
            "ru": ("Деловые запросы", "По вопросам сотрудничества или оптовых закупок используйте форму и выберите соответствующий тип запроса на странице «Запросить цену»."),
            "uz": ("Biznes so'rovlari", "Biznes yoki ulgurji so'rovlar uchun formadan foydalaning va «Narx so'rash» sahifasida mos so'rov turini tanlang."),
        },
    ),
    ("faq", "What materials are your containers made of?", "All MARU containers are made of food-safe polypropylene.", {"ru": ("Из каких материалов изготовлены ваши контейнеры?", "Все контейнеры MARU изготовлены из пищевого полипропилена."), "uz": ("Idishlaringiz qanday materialdan tayyorlangan?", "Barcha MARU idishlari oziq-ovqat uchun xavfsiz polipropilendan tayyorlangan.")}),
    ("faq", "What sizes are available?", "Our containers range from 350 ml to 1900 ml — see the Shop page for the full current lineup.", {"ru": ("Какие размеры доступны?", "Наши контейнеры выпускаются объёмом от 350 мл до 1900 мл — актуальный ассортимент смотрите на странице «Магазин»."), "uz": ("Qanday o'lchamlar mavjud?", "Idishlarimiz hajmi 350 ml dan 1900 ml gacha — joriy assortimentni «Do'kon» sahifasida ko'rishingiz mumkin.")}),
    ("faq", "Are the containers microwave-safe?", "Polypropylene containers are generally microwave-safe; check the specific product page for details.", {"ru": ("Можно ли использовать контейнеры в микроволновой печи?", "Полипропиленовые контейнеры, как правило, подходят для микроволновой печи; подробности смотрите на странице конкретного товара."), "uz": ("Idishlarni mikroto'lqinli pechda ishlatish mumkinmi?", "Polipropilen idishlar odatda mikroto'lqinli pech uchun xavfsiz; batafsil ma'lumotni tegishli mahsulot sahifasida ko'ring.")}),
    ("faq", "How do I check my order status?", "Log in and visit your Orders page, or use the order confirmation link you received.", {"ru": ("Как узнать статус моего заказа?", "Войдите в аккаунт и откройте страницу «Заказы» или воспользуйтесь ссылкой из письма с подтверждением заказа."), "uz": ("Buyurtmam holatini qanday bilaman?", "Hisobingizga kiring va «Buyurtmalar» sahifasini oching yoki buyurtma tasdig'i xabaridagi havoladan foydalaning.")}),
    ("faq", "Can I change my order after placing it?", "Contact us as soon as possible — orders that haven't shipped yet can often still be adjusted.", {"ru": ("Можно ли изменить заказ после оформления?", "Свяжитесь с нами как можно скорее — в заказ, который ещё не отправлен, часто можно внести изменения."), "uz": ("Buyurtmani rasmiylashtirgandan keyin o'zgartirish mumkinmi?", "Iloji boricha tezroq biz bilan bog'laning — hali jo'natilmagan buyurtmaga ko'pincha o'zgartirish kiritish mumkin.")}),
    ("faq", "Can I cancel my order?", "Orders that haven't shipped can be cancelled from the order status page.", {"ru": ("Можно ли отменить заказ?", "Заказ, который ещё не отправлен, можно отменить на странице статуса заказа."), "uz": ("Buyurtmani bekor qilish mumkinmi?", "Hali jo'natilmagan buyurtmani buyurtma holati sahifasida bekor qilish mumkin.")}),
    ("faq", "What payment methods do you accept?", "Available methods are shown at checkout and on the Payment page — they vary based on current configuration.", {"ru": ("Какие способы оплаты вы принимаете?", "Доступные способы оплаты отображаются при оформлении заказа и на странице «Оплата» — они зависят от текущих настроек."), "uz": ("Qanday to'lov usullarini qabul qilasiz?", "Mavjud to'lov usullari buyurtma rasmiylashtirishda va «To'lov» sahifasida ko'rsatiladi — ular joriy sozlamalarga bog'liq.")}),
    ("faq", "Is my payment information secure?", "Payments are processed directly by our payment providers; we never store your card details.", {"ru": ("Безопасны ли мои платёжные данные?", "Платежи обрабатываются напрямую платёжными провайдерами; данные вашей карты мы не храним."), "uz": ("To'lov ma'lumotlarim xavfsizmi?", "To'lovlar to'g'ridan-to'g'ri to'lov provayderlari orqali amalga oshiriladi; karta ma'lumotlaringizni biz saqlamaymiz.")}),
    ("faq", "Can I pay by invoice for a wholesale order?", "Yes — invoice payment is available for approved wholesale and distributor accounts.", {"ru": ("Можно ли оплатить оптовый заказ по счёту?", "Да — оплата по счёту доступна для одобренных оптовых клиентов и дистрибьюторов."), "uz": ("Ulgurji buyurtmani hisob-faktura orqali to'lash mumkinmi?", "Ha — hisob-faktura orqali to'lash tasdiqlangan ulgurji xaridorlar va distribyutorlar uchun mavjud.")}),
    ("faq", "How long does delivery take?", "Delivery times depend on your location and chosen method — see the Delivery page for details.", {"ru": ("Сколько занимает доставка?", "Сроки доставки зависят от вашего местоположения и выбранного способа — подробности на странице «Доставка»."), "uz": ("Yetkazib berish qancha vaqt oladi?", "Yetkazib berish muddati joylashuvingiz va tanlangan usulga bog'liq — batafsil ma'lumot «Yetkazib berish» sahifasida.")}),
    ("faq", "Do you ship internationally?", "Yes, to a growing list of countries — see the Delivery page for the current list.", {"ru": ("Осуществляете ли вы международную доставку?", "Да, в постоянно растущий список стран — актуальный перечень смотрите на странице «Доставка»."), "uz": ("Xalqaro yetkazib berish mavjudmi?", "Ha, kengayib borayotgan davlatlar ro'yxatiga — joriy ro'yxatni «Yetkazib berish» sahifasida ko'ring.")}),
    ("faq", "Can I track my shipment?", "You can check your order's status from your Orders page.", {"ru": ("Можно ли отследить мою посылку?", "Статус заказа можно посмотреть на странице «Заказы»."), "uz": ("Jo'natmamni kuzatib borish mumkinmi?", "Buyurtma holatini «Buyurtmalar» sahifasida tekshirishingiz mumkin.")}),
    ("faq", "What is your return policy?", "See the Returns page for full details on conditions, timeframe, and procedure.", {"ru": ("Каковы ваши условия возврата?", "Подробные условия, сроки и порядок возврата смотрите на странице «Возврат»."), "uz": ("Qaytarish siyosatingiz qanday?", "Shartlar, muddatlar va tartib haqida to'liq ma'lumotni «Qaytarish» sahifasida ko'ring.")}),
    ("faq", "Who pays for return shipping?", "This depends on the reason for the return — we'll confirm details when you contact us.", {"ru": ("Кто оплачивает доставку при возврате?", "Это зависит от причины возврата — детали мы уточним при обращении к нам."), "uz": ("Qaytarish uchun yetkazib berishni kim to'laydi?", "Bu qaytarish sababiga bog'liq — tafsilotlarni murojaat qilganingizda aniqlashtiramiz.")}),
    ("faq", "How long do refunds take?", "Refunds are processed once the return is received and inspected.", {"ru": ("Как быстро возвращаются деньги?", "Возврат средств производится после получения и проверки возвращённого товара."), "uz": ("Pulni qaytarish qancha vaqt oladi?", "Pul qaytarilgan mahsulot qabul qilinib, tekshirilgandan so'ng qaytariladi.")}),
    ("faq", "How do I get wholesale pricing?", "Submit a request on the Wholesale page and our team will follow up with pricing.", {"ru": ("Как получить оптовые цены?", "Оставьте заявку на странице «Оптом», и наша команда свяжется с вами с расчётом цен."), "uz": ("Ulgurji narxlarni qanday olaman?", "«Ulgurji» sahifasida so'rov qoldiring — jamoamiz siz bilan narxlar bo'yicha bog'lanadi.")}),
    ("faq", "Is there a minimum order quantity?", "MOQ varies by product — mention your target volume when requesting a quote.", {"ru": ("Есть ли минимальный объём заказа?", "Минимальный объём зависит от товара — укажите желаемый объём при запросе цены."), "uz": ("Minimal buyurtma miqdori bormi?", "Minimal miqdor mahsulotga qarab farq qiladi — narx so'raganingizda kerakli hajmni ko'rsating.")}),
    ("faq", "Do you offer custom packaging?", "Custom packaging is available on request for larger orders.", {"ru": ("Предлагаете ли вы индивидуальную упаковку?", "Индивидуальная упаковка доступна по запросу для крупных заказов."), "uz": ("Maxsus qadoqlash xizmati bormi?", "Yirik buyurtmalar uchun maxsus qadoqlash so'rov bo'yicha mavjud.")}),
    ("faq", "Which countries do you ship to?", "See the Delivery page for the current list of supported countries.", {"ru": ("В какие страны вы доставляете?", "Актуальный список стран смотрите на странице «Доставка»."), "uz": ("Qaysi davlatlarga yetkazib berasiz?", "Qo'llab-quvvatlanadigan davlatlarning joriy ro'yxatini «Yetkazib berish» sahifasida ko'ring.")}),
    ("faq", "Are prices shown in my local currency?", "Yes — use the currency switcher in the header to see prices in your preferred currency.", {"ru": ("Отображаются ли цены в моей местной валюте?", "Да — выберите нужную валюту в переключателе валют в шапке сайта."), "uz": ("Narxlar mening mahalliy valyutamda ko'rsatiladimi?", "Ha — sahifa tepasidagi valyuta almashtirgichdan o'zingizga qulay valyutani tanlang.")}),
    ("faq", "Is the site available in my language?", "MARU is available in Russian, Uzbek, and English — use the language switcher in the header.", {"ru": ("Доступен ли сайт на моём языке?", "MARU доступен на русском, узбекском и английском языках — используйте переключатель языка в шапке сайта."), "uz": ("Sayt mening tilimda mavjudmi?", "MARU rus, o'zbek va ingliz tillarida mavjud — sahifa tepasidagi til almashtirgichdan foydalaning.")}),
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

    page_orders: dict[str, int] = {}
    for page, title, body, translations in PAGE_SECTIONS:
        page_orders[page] = page_orders.get(page, 0) + 1
        section = PageSection(page=page, title=title, body=body, sort_order=page_orders[page])
        db.add(section)
        db.flush()
        for locale, (t_title, t_body) in translations.items():
            db.add(PageSectionTranslation(section_id=section.id, locale=locale, title=t_title, body=t_body))

    db.commit()
    print("Seeded dev catalog.")


if __name__ == "__main__":
    run()
