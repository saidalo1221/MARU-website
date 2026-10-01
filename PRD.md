<!-- BUILD STATUS START -->
## BUILD STATUS (agent-maintained)
Legend: [x] built and tested, [!] blocked (reason given), [ ] not built yet.
Details of how each was verified are in git history; assumptions are in NOTES.md.

### TZ2 UI/UX
- [x] TZ2 §5-7 Header (Shop/Business/About/Support/Blog menus, country selector), mobile header, footer columns + bottom row
- [x] TZ2 §8 Home page (11 blocks)
- [x] TZ2 §9, §50 Catalog: filters (capacity, color, price, category, availability), sort, pagination, mobile bottom sheet
- [x] TZ2 §10 Category page (H1, description, image, SEO content, FAQ)
- [x] TZ2 §11, §48-49 Product card (price, old price, discount, availability, rating, Add to Cart, Quick View, Wishlist), badges
- [x] TZ2 §12-17 Product page (gallery, variants, quantity tiers, CTAs incl. Request a Quote, delivery block)
- [x] TZ2 §18-19 Search (autocomplete, suggestions, SKU, typo tolerance, results page)
- [x] TZ2 §20-21 Cart and upsell
- [x] TZ2 §22-25 Checkout, payment states, order success
- [x] TZ2 §26-29 Login/registration, account (dashboard, orders, wishlist, addresses, profile)
- [x] TZ2 §30-33 B2B, wholesale, request a quote, distributor
- [x] TZ2 §34-40 About (company, manufacturing, quality), contact, delivery, payment, returns, FAQ by category, blog
- [x] TZ2 §41-42 International UX (country, language, currency)
- [x] TZ2 §43 CRO (packs, quantity discounts, reorder, free-shipping threshold)
- [x] TZ2 §45-47, §60 Design system and tokens, buttons, form components
- [x] TZ2 §51-56 Responsive, loading/empty/error states, accessibility
- [x] TZ2 §62-63 SEO structure, analytics events
- [!] TZ2 §59, §65 Figma file, interactive prototype, wireframes and developer handoff — BLOCKED: these are designer deliverables (need a designer and Figma); tokens and the component kit are in DESIGN_SYSTEM.md

### TZ3 Architecture
- [x] TZ3 §16-42 Data model (see PRD_AUDIT.md) — BLOCKED (on hold by owner): payments ledger / orders.payment_status not built; the rest of the data model is in place
- [x] TZ3 §43-53 API design (filters, sorting whitelist, pagination limit, error format)
- [x] TZ3 §54-58 Auth, RBAC, admin MFA
- [x] TZ3 §59-68 Order engine, state machine, idempotency, inventory
- [x] TZ3 §69-75 Pricing, i18n, currency, tax, timezone
- [x] TZ3 §76-83 Security, audit log, backups
- [x] TZ3 §84-92 Performance, caching, async, logging
- [x] TZ3 §93-101 Alerting, environments, CI/CD, tests, migrations
- [x] TZ3 §102-105 GDPR/privacy, admin architecture, analytics

### TZ4 Integrations
- [x] TZ4 §1-5 Integration layer, adapter interfaces, master-data matrix
- [!] TZ4 §6-13 ERP/1C — BLOCKED: no ERP/1C API spec, endpoint or credentials; adapter interface, id mapping and OrderPaid event are ready for the connector
- [x] TZ4 §14-18 CRM, RFQ, attribution
- [!] TZ4 §19-28 Payments — BLOCKED: BLOCKED: Payme/Click/Stripe/PayPal are built from public docs but unverified (no sandbox credentials). The payments ledger is built; the PRD webhook path /integrations/payments/{provider}/webhook was not added (Payme/Click keep their /payments/* protocol endpoints)
- [x] TZ4 §29-33 Shipping
- [!] TZ4 §34-39 Marketplace/Uzum — BLOCKED: no Uzum/marketplace seller API access or docs; MarketplaceAdapter interface is ready
- [!] TZ4 §40-44 SMS, email, templates, WhatsApp, Telegram — PARTLY BLOCKED: email + templates done; SMS/WhatsApp/Telegram need provider accounts and credentials (MessagingAdapter ready)
- [!] TZ4 §45-49 Analytics: GA4, GTM, Meta, server-side — PARTLY BLOCKED: GTM/GA4 events stored server-side; forwarding to GA4/Meta needs measurement ids, API secrets and a pixel
- [x] TZ4 §50-69 Webhooks, retry, DLQ, logging, health, reconciliation
- [x] TZ4 §70-93 Contracts, data mapping, documents, B2B, testing
<!-- BUILD STATUS END -->

[8/15/2026 1:57 PM] Ada: ТЕХНИЧЕСКОЕ ЗАДАНИЕ №2
UI/UX интернет-магазина MARU
Проект: MARU E-commerce
Документ: UI/UX Specification
Версия: 1.0
Основание: ТЗ №1 «Функциональность и бизнес-логика интернет-магазина MARU»
Назначение: передача дизайнеру, UX/UI-команде и frontend-разработчикам
1. ЦЕЛЬ ДОКУМЕНТА
Данное ТЗ определяет пользовательский интерфейс и пользовательский опыт интернет-магазина MARU.
Сайт должен быть спроектирован не как простой каталог пластиковых контейнеров, а как международная e-commerce платформа, поддерживающая:
B2C;
B2B;
оптовые продажи;
продажи дистрибьюторам;
экспорт;
локальные продажи в Узбекистане;
международные продажи;
повторные покупки;
будущую интеграцию с marketplace.
Основной UX-принцип:
Пользователь должен максимально быстро понять, что продаёт MARU, выбрать подходящий товар, увидеть цену и условия доставки и оформить заказ с минимальным количеством действий.
2. ОСНОВНЫЕ UX-ПРИНЦИПЫ
Интерфейс должен соответствовать следующим принципам:
Mobile First
Простота.
Минимальное количество действий до покупки.
Чёткая визуальная иерархия.
Максимальная прозрачность цены.
Понятная информация о наличии.
Понятная информация о доставке.
Быстрый поиск товара.
Минимум отвлекающих элементов.
Разделение B2C и B2B-сценариев.
Международная локализация.
Единая визуальная система.
3. ЦЕЛЕВЫЕ ПОЛЬЗОВАТЕЛИ
3.1. B2C
Конечный покупатель, приобретающий небольшое количество контейнеров.
Основная задача:
найти → выбрать → купить → получить.
3.2. B2B
Ресторан, кафе, catering, магазин, производственная компания.
Основная задача:
найти → определить количество → получить цену → оформить закупку.
3.3. Wholesale
Покупатель крупной партии.
Основная задача:
выбрать ассортимент → получить оптовую цену → запросить предложение.
3.4. Distributor
Потенциальный региональный или международный партнёр.
Основная задача:
узнать условия → оставить заявку → связаться с менеджером.
4. INFORMATION ARCHITECTURE
Основная структура:
HOME │ ├── SHOP │ ├── Food Containers │ │ ├── 350 ml │ │ ├── 470 ml │ │ ├── 800 ml │ │ ├── 1000 ml │ │ └── 1900 ml │ │ │ ├── Sets / Packs │ └── New / Featured │ ├── BUSINESS │ ├── Wholesale │ ├── B2B │ ├── Request a Quote │ └── Distributor │ ├── ABOUT MARU │ ├── Company │ ├── Manufacturing │ └── Quality │ ├── SUPPORT │ ├── Delivery │ ├── Payment │ ├── Returns │ ├── FAQ │ └── Contact │ ├── BLOG │ └── ACCOUNT ├── Orders ├── Wishlist ├── Addresses └── Profile 
5. HEADER
Desktop Header должен содержать:
Верхняя информационная панель
При необходимости:
доставка;
специальные предложения;
B2B;
международная доставка.
Основной Header
Слева:
MARU Logo
Центр:
Shop;
Business;
About;
Support;
Blog.
Справа:
Search;
Country;
Language;
Currency;
Account;
Wishlist;
Cart.
6. MOBILE HEADER
На мобильном устройстве:
Logo | Search | Cart | Menu
Menu открывает полноэкранную или slide-in навигацию.
Порядок:
Shop
Categories
Business
About MARU
Support
Blog
Account
Language
Currency
Country
7. FOOTER
Footer должен содержать четыре основных колонки.
Shop
All Products;
Food Containers;
Sets;
New Products.
Business
Wholesale;
B2B;
Distributor;
Request a Quote.
Support
Delivery;
Payment;
Returns;
FAQ;
Contact.
MARU
About;
Manufacturing;
Quality;
Blog.
Нижняя часть:
Privacy Policy;
Terms;
Cookies;
Copyright;
payment icons;
social media.
8. HOME PAGE
Цель
Показать ценность MARU и максимально быстро направить пользователя к покупке.
Структура сверху вниз
8.1. Header
Основная навигация.
8.2. Hero
Содержит:
основной визуальный образ продукта;
короткий value proposition;
основной CTA;
дополнительный CTA.
Основной CTA:
Shop Containers
Второй CTA:
For Business
Hero не должен быть перегружен текстом.
8.3. Product Categories
Карточки:
350 ml;
470 ml;
800 ml;
1000 ml;
1900 ml.
8.4. Best Sellers
Карточки товаров.
8.5. Why MARU
Преимущества:
качественный материал;
собственное производство;
[8/15/2026 1:57 PM] Ada: широкий ассортимент;
стабильное качество;
B2B/Wholesale;
международные поставки.
8.6. Sets
Продвижение Pack 3 / Pack 5 / Pack 7.
8.7. B2B Block
CTA:
Buy Wholesale
8.8. Manufacturing / Quality
Визуальный блок с производством.
CTA:
Learn More
8.9. Reviews
Отзывы клиентов.
8.10. FAQ
Краткий FAQ.
8.11. Final CTA
Shop MARU Containers
9. CATALOG PAGE
Цель
Предоставить полный каталог с удобной фильтрацией.
Структура:
Breadcrumbs;
H1;
description;
filters;
sorting;
product grid;
pagination.
Desktop
Слева:
Filters.
Справа:
Product Grid.
Mobile
Фильтры открываются через кнопку:
Filters
Сортировка:
Sort
10. CATEGORY PAGE
Категория должна содержать:
Breadcrumb.
H1.
Category description.
Category image.
Filters.
Sort.
Product grid.
SEO content.
FAQ.
11. PRODUCT CARD
Каждая карточка должна содержать:
product image;
product name;
capacity;
price;
old price при наличии;
discount;
availability;
rating;
Add to Cart.
Дополнительно:
Quick View;
Wishlist.
Карточка не должна содержать чрезмерное количество информации.
12. PRODUCT PAGE
Это основной коммерческий экран сайта.
Desktop Layout
Левая часть:
Product Gallery
Правая:
product name;
SKU;
rating;
price;
old price;
discount;
availability;
variant selector;
quantity;
Add to Cart;
Buy Now;
delivery information.
Ниже:
description;
specifications;
benefits;
delivery;
reviews;
FAQ;
recommended products.
13. PRODUCT GALLERY
Поддержать:
основное изображение;
thumbnails;
zoom;
product-in-use;
dimensions;
packaging;
video.
На мобильном устройстве — горизонтальный swipe gallery.
14. ВЫБОР ВАРИАНТА
Если доступны варианты:
volume;
color;
pack;
SKU.
Недоступный вариант должен отображаться как unavailable.
После выбора варианта:
цена;
SKU;
наличие;
изображение
обновляются без перезагрузки страницы.
15. QUANTITY
Количество должно поддерживать:
− 1 +
При B2B/Wholesale могут отображаться:
minimum order quantity;
quantity discounts.
Например:
1–9 $X 10–49 $Y 50–199 $Z 200+ $W 
16. CTA PRODUCT PAGE
Основная кнопка:
Add to Cart
Вторая:
Buy Now
Для B2B:
Request a Quote
CTA должен оставаться визуально заметным на мобильном устройстве.
17. DELIVERY BLOCK
На Product Page пользователь должен видеть:
доступность доставки;
ориентировочный срок;
стоимость;
country selector.
Например:
Deliver to Uzbekistan
или
Deliver to Germany
18. SEARCH
Search должен поддерживать:
autocomplete;
product suggestions;
categories;
SKU;
typo tolerance.
При вводе:
1000
показываются соответствующие товары.
19. SEARCH RESULTS
Структура:
Search field;
query;
number of results;
filters;
sorting;
products.
При отсутствии результатов:
No products found
и предложения:
изменить запрос;
посмотреть категории;
перейти к популярным товарам.
20. CART
Корзина должна показывать:
product;
image;
variant;
quantity;
unit price;
discount;
subtotal;
remove;
save for later.
Справа:
subtotal;
discount;
estimated delivery;
total;
Checkout.
CTA:
Proceed to Checkout
21. CART UPSELL
Перед checkout можно показывать:
Frequently Bought Together
или:
You may also like
Но upsell не должен препятствовать оформлению заказа.
22. CHECKOUT
Checkout должен быть максимально коротким.
Рекомендуемый порядок:
Step 1
Contact information.
Step 2
Shipping address.
Step 3
Delivery method.
Step 4
Payment.
Step 5
Order review.
На мобильном устройстве желательно использовать single-page checkout либо очень короткий пошаговый checkout.
23. CHECKOUT UX
Необходимо постоянно показывать:
товары;
subtotal;
delivery;
discount;
tax при необходимости;
total.
Не заставлять пользователя возвращаться назад для проверки стоимости.
24. PAYMENT
После выбора метода оплаты:
Pay Now
При успешной оплате:
Payment Successful
При ошибке:
Payment Failed
Пользователь должен получить возможность повторить оплату.
25. ORDER SUCCESS
После заказа:
Order Confirmed
Показать:
Order Number;
дата;
товары;
сумма;
способ доставки;
[8/15/2026 1:57 PM] Ada: payment status;
shipping address;
estimated delivery.
CTA:
Track Order
Дополнительно:
Continue Shopping
26. LOGIN / REGISTRATION
Регистрация не обязательна для покупки.
Предусмотреть:
Login
e-mail/phone;
password;
forgot password.
Registration
name;
e-mail;
phone;
password.
После Guest Checkout предложить:
Create an account to track your orders faster.
27. ACCOUNT
Dashboard содержит:
recent orders;
order status;
wishlist;
addresses;
profile;
account settings.
28. ORDERS
Список:
Order Number;
date;
amount;
status;
tracking.
Каждый заказ открывается в отдельной странице.
29. WISHLIST
Показывает:
product;
price;
availability;
Add to Cart;
Remove.
Если товар закончился:
Notify me when available
30. B2B PAGE
B2B должен быть отдельным коммерческим разделом.
Hero:
MARU for Business
Показать:
wholesale;
bulk orders;
custom quantities;
distributor opportunities;
international supply.
CTA:
Request a Quote
31. WHOLESALE PAGE
Показать:
преимущества;
MOQ;
pricing tiers;
available products;
packaging;
delivery;
contact form.
CTA:
Get Wholesale Price
32. REQUEST A QUOTE
Форма:
Name;
Company;
Country;
City;
Email;
Phone;
Products;
Quantity;
Comment.
После отправки:
Request submitted successfully.
Пользователь получает номер заявки.
33. DISTRIBUTOR PAGE
Страница предназначена для потенциальных партнёров.
Содержит:
MARU;
производственные возможности;
ассортимент;
рынки;
условия сотрудничества;
логистика;
форма заявки.
CTA:
Become a Distributor
34. ABOUT MARU
Содержит:
история;
компания;
производство;
оборудование;
качество;
продукция;
рынки.
Важно использовать реальные фотографии производства, а не исключительно стоковые изображения.
35. CONTACT
Содержит:
телефон;
e-mail;
адрес;
карта;
контактная форма;
business inquiries;
wholesale inquiries.
36. DELIVERY
Информация должна быть разделена:
Uzbekistan
International
Показать:
сроки;
способы;
стоимость;
tracking;
ограничения.
37. PAYMENT PAGE
Показать доступные методы оплаты для выбранной страны.
Важно:
не показывать пользователю способы оплаты, которые недоступны в его регионе.
38. RETURNS
Объяснить:
условия возврата;
сроки;
процедуру;
исключения;
контакт.
39. FAQ
FAQ должен быть разбит по категориям:
Products;
Orders;
Payment;
Delivery;
Returns;
Wholesale;
International.
40. BLOG
Структура:
Blog Home;
Categories;
Article;
Related Articles.
Карточка статьи:
image;
category;
title;
short description;
date;
Read More.
41. INTERNATIONAL UX
В верхней части сайта предусмотреть:
Country | Language | Currency
Например:
UZ | RU | UZS
При выборе Германии:
DE | EN | EUR
Смена страны может менять:
доступность;
цену;
валюту;
доставку;
налоги;
оплату.
42. COUNTRY SELECTION
При первом посещении:
если страна определена автоматически, показать ненавязчивое предложение:
We detected that you are in Uzbekistan. Shop in UZS?
Пользователь может изменить страну вручную.
Нельзя блокировать просмотр сайта обязательным выбором страны.
43. CRO
Основные цели
Conversion Rate
Уменьшить количество действий до покупки.
AOV
Использовать:
packs;
quantity discounts;
frequently bought together;
free shipping threshold.
Repeat Purchase
Использовать:
reorder;
account;
saved products;
personalized recommendations.
B2B Leads
Использовать:
Request Quote;
Wholesale CTA;
Distributor CTA.
44. TRUST ELEMENTS
На коммерческих страницах использовать реальные доказательства:
производитель;
собственное производство;
реальные фотографии;
характеристики;
сертификаты — только если они реально имеются;
отзывы;
условия доставки;
прозрачные контакты.
Не использовать неподтверждённые claims.
45. DESIGN SYSTEM
45.1. Typography
Необходимо определить:
font family;
H1;
H2;
H3;
body;
caption;
buttons;
labels.
Финальные значения утверждаются дизайнером.
45.2. Colors
Фирменные цвета MARU не придумывать без брендбука.
До получения брендбука использовать временные design tokens.
[8/15/2026 1:57 PM] Ada: После предоставления брендбука значения заменяются централизованно.
46. BUTTONS
Минимум:
Primary;
Secondary;
Tertiary;
Danger;
Disabled.
Каждая кнопка должна иметь состояния:
default;
hover;
active;
focus;
loading;
disabled.
47. FORM COMPONENTS
Поддержать:
input;
textarea;
select;
checkbox;
radio;
dropdown;
phone input;
country selector.
Каждое поле должно иметь:
label;
placeholder;
helper text;
error;
success;
disabled state.
48. PRODUCT CARD COMPONENT
Компонент должен быть единым во всём сайте.
Варианты:
standard;
compact;
horizontal;
recommendation.
49. BADGES
Предусмотреть:
New;
Best Seller;
Sale;
Limited;
In Stock;
Out of Stock.
Использовать badges экономно.
50. FILTERS
Фильтры:
capacity;
color;
material;
price;
availability;
category.
Mobile:
Filter
открывает bottom sheet или full-screen filter panel.
51. RESPONSIVE DESIGN
Минимально предусмотреть:
Mobile
320–767 px
Tablet
768–1023 px
Desktop
1024+ px
Large Desktop
1440+ px
Точные breakpoints утверждаются frontend-командой на основании design system.
52. MOBILE FIRST
На мобильном устройстве приоритет:
Product.
Price.
Availability.
Add to Cart.
Delivery.
Description.
Specifications.
Reviews.
Необходимо исключить горизонтальный overflow.
53. LOADING STATES
Каждый динамический компонент должен иметь loading state.
Использовать skeleton вместо пустого экрана там, где это улучшает UX.
54. EMPTY STATES
Предусмотреть:
empty cart;
empty wishlist;
no orders;
no search results;
no products;
no notifications.
Каждый empty state должен содержать:
объяснение;
следующий шаг;
CTA.
55. ERROR STATES
Ошибки должны быть понятны обычному пользователю.
Не показывать:
500 Internal Server Error
вместо пользовательского сообщения.
Например:
Something went wrong. Please try again.
И кнопка:
Try Again
56. ACCESSIBILITY
Минимально соблюдать WCAG 2.1 AA.
Предусмотреть:
keyboard navigation;
visible focus;
sufficient contrast;
semantic headings;
alt text;
accessible forms;
error messages;
screen-reader compatibility;
touch targets appropriate for mobile.
57. USER FLOWS
B2C
Landing ↓ Category ↓ Product ↓ Add to Cart ↓ Cart ↓ Checkout ↓ Payment ↓ Order Confirmation ↓ Delivery ↓ Review ↓ Repeat Purchase 
B2B
Landing ↓ B2B ↓ Products ↓ Request Quote ↓ CRM ↓ Manager ↓ Commercial Offer ↓ Payment ↓ Shipment 
Distributor
Distributor Page ↓ Application ↓ CRM ↓ Manager ↓ Negotiation ↓ Agreement 
58. UI COMPONENT INVENTORY
Минимальный набор:
Header;
Mobile Header;
Footer;
Navigation;
Breadcrumb;
Search;
Product Card;
Product Gallery;
Product Selector;
Price Block;
Quantity Selector;
CTA Button;
Cart;
Checkout;
Form;
Modal;
Drawer;
Filter;
Sort;
Pagination;
Tabs;
Accordion;
Badge;
Alert;
Toast;
Review;
Rating;
Country Selector;
Language Selector;
Currency Selector.
Все компоненты должны быть reusable.
59. DESIGN FILE STRUCTURE
Рекомендуемая структура Figma:
00 — Cover 01 — Design Tokens 02 — Components 03 — Patterns 04 — Desktop 05 — Tablet 06 — Mobile 07 — User Flows 08 — Prototype 09 — Developer Handoff 
60. DESIGN TOKENS
Создать централизованные tokens:
Colors Typography Spacing Radius Shadows Borders Breakpoints Grid Animation 
Это позволит изменить дизайн всей платформы без ручного редактирования каждого экрана.
61. ANIMATION
Анимации должны использоваться функционально:
add to cart;
modal;
drawer;
dropdown;
page transitions;
loading.
Не использовать тяжёлые анимации, ухудшающие скорость сайта.
62. SEO/UX
UI должен поддерживать SEO-структуру:
один основной H1;
логические H2/H3;
breadcrumbs;
crawlable navigation;
indexable category pages;
SEO-friendly content blocks.
63. ANALYTICS EVENTS
UX должен предусматривать события:
view_product;
select_variant;
add_to_cart;
remove_from_cart;
begin_checkout;
add_payment_info;
purchase;
search;
wishlist_add;
request_quote;
distributor_request;
newsletter_signup.
64. UX ACCEPTANCE CRITERIA
[8/15/2026 1:57 PM] Ada: UI/UX считается готовым, если:
пользователь понимает назначение сайта;
пользователь может найти товар максимум за несколько действий;
категория понятна;
карточка товара содержит необходимую коммерческую информацию;
цена очевидна;
наличие очевидно;
доставка понятна;
checkout не содержит лишних шагов;
B2B путь отделён от B2C;
мобильная версия полностью функциональна;
предусмотрены loading/empty/error/success states;
все ключевые компоненты имеют состояния;
интерфейс соответствует accessibility requirements;
desktop и mobile имеют согласованную логику;
все основные страницы имеют готовые wireframe-level specifications.
65. ОБЯЗАТЕЛЬНЫЕ UX-АРТЕФАКТЫ ДЛЯ ДИЗАЙНЕРА
До начала полноценной визуальной разработки необходимо подготовить:
Sitemap.
User Flow.
Wireframes.
Design System.
Component Library.
Desktop layouts.
Mobile layouts.
Interactive prototype.
Developer handoff.
66. ПРИОРИТЕТЫ UX
P0 — критично
Product;
Cart;
Checkout;
Payment;
Order;
Mobile;
Search;
Navigation.
P1 — важно
Wishlist;
Reviews;
B2B;
Wholesale;
Request Quote;
International UX.
P2 — развитие
Blog;
Advanced recommendations;
Loyalty;
personalization;
advanced distributor portal.
67. ОСНОВНОЙ КРИТЕРИЙ КАЧЕСТВА
Дизайн должен отвечать на пять вопросов пользователя практически сразу:
Что это?
Сколько стоит?
Какой вариант мне подходит?
Когда я получу товар?
Как купить?
Если пользователь не может быстро ответить на эти вопросы, соответствующий UX необходимо переработать.
68. ИТОГОВАЯ АРХИТЕКТУРА UX
MARU │ ┌──────────┴──────────┐ │ │ B2C B2B │ │ Catalog Wholesale │ │ Product Request Quote │ │ Cart CRM │ │ Checkout Manager │ │ Payment Offer │ │ Order Payment │ │ Delivery Shipment 
69. СВЯЗЬ С ТЗ №1
ТЗ №2 не должно дублировать бизнес-функциональность ТЗ №1.
Связь документов:
ТЗ №1
определяет:

что система умеет делать.
ТЗ №2
определяет
:
где и каким образом пользователь получает доступ к этой функции
.
ТЗ №3
определя
ет:
как функция реализуется техничес
ки.
Таким образом, каждый функциональный модуль из ТЗ №1 должен иметь соответствующий UI/UX-представитель в ТЗ №2.
70. РЕЗУЛЬТАТ ТЗ №2
После утверждения данного документа дизайнерская команда должна иметь возможность создать полный UX/UI-проект интернет-магазина MARU, а frontend-команда — реализовать интерфейс без самостоятельного проектирования пользовательской логики.
ТЗ №2 является основанием для разработки Figma-дизайна, прототипа и последующей frontend-реализации.

ТЕХНИЧЕСКОЕ ЗАДАНИЕ №3
Техническая архитектура интернет-магазина MARU E-commerce
Проект: MARU E-commerce
Документ: System Architecture & Technical Specification
Версия: 1.0
Основание: ТЗ №1 — функциональность и бизнес-логика; ТЗ №2 — UI/UX
Назначение: CTO, Solution Architect, Backend, Frontend, DevOps, QA и Security-команда
1. НАЗНАЧЕНИЕ СИСТЕМЫ
MARU E-commerce — централизованная коммерческая платформа для продажи пластиковых пищевых контейнеров собственного производства.
Система должна поддерживать:
B2C;
B2B;
Wholesale;
Distributor;
локальные продажи в Узбекистане;
международные продажи;
несколько валют;
несколько языков;
несколько складов;
различные уровни цен;
онлайн-оплату;
доставку;
CRM;
ERP/1С;
marketplace;
аналитику.
Архитектура должна позволять добавлять новые рынки без переписывания основной бизнес-логики.
2. АРХИТЕКТУРНЫЕ ПРИНЦИПЫ
Система строится на следующих принципах:
API-first.
Mobile-first.
Security-by-design.
Single Source of Truth для критических данных.
Разделение frontend и backend.
Модульная бизнес-логика.
Асинхронная обработка тяжёлых операций.
Idempotency для платежей и заказов.
Auditability.
Horizontal scalability.
Stateless application layer.
Возможность дальнейшего выделения отдельных сервисов.
3. ВЫБОР АРХИТЕКТУРНОЙ МОДЕЛИ
Рассмотрены три варианта.
3.1. Классический Monolith
Весь backend является единым приложением без чёткого разделения модулей.
[8/15/2026 1:57 PM] Ada: Преимущества
быстрое начало разработки;
простое развертывание;
низкая стоимость инфраструктуры.
Недостатки
сложнее масштабировать отдельные модули;
сильная связанность;
сложнее развивать крупную систему.
Для MARU как долгосрочную архитектуру не рекомендуется.
4. MICROSERVICES
Каждый модуль работает как отдельный сервис.
Например:
Product Service;
Order Service;
Payment Service;
Inventory Service;
Customer Service.
Преимущества
независимое масштабирование;
независимые deployment;
изоляция сервисов.
Недостатки
высокая сложность;
distributed transactions;
service discovery;
сложнее debugging;
больше DevOps;
выше стоимость.
Для MVP MARU преждевременно.
5. РЕКОМЕНДУЕМАЯ АРХИТЕКТУРА — MODULAR MONOLITH + API-FIRST
Для MARU рекомендуется:
Modular Monolith на первом этапе с возможностью постепенного перехода к Microservices.
Backend является одним deployable application, но бизнес-логика разделена на независимые модули.
Frontend │ ▼ API Gateway │ ▼ MARU Commerce API │ ┌────────────────┼─────────────────┐ │ │ │ Catalog Orders Customers │ │ │ Pricing Inventory B2B │ │ │ Reviews Payments Shipping │ │ │ └────────────────┼─────────────────┘ │ ┌────────────┼─────────────┐ ▼ ▼ ▼ PostgreSQL Redis Object Storage │ ▼ Queue/Workers │ ┌──────────────┼──────────────┐ ▼ ▼ ▼ ERP CRM Payments 
6. ПОЧЕМУ MODULAR MONOLITH
Для текущего бизнеса MARU это оптимальный баланс между:
стоимостью;
скоростью разработки;
простотой сопровождения;
производительностью;
возможностью масштабирования.
При росте нагрузки отдельные модули можно вынести в самостоятельные сервисы.
Первыми кандидатами на выделение:
Search;
Notifications;
Payment;
Shipping;
Marketplace Integration;
Analytics.
7. FRONTEND
Рекомендуемый stack
Next.js + React + TypeScript
Причины:
SSR;
SEO;
высокая производительность;
хорошая поддержка e-commerce;
TypeScript;
component architecture;
responsive UI;
удобная интеграция с API.
Frontend не должен содержать критическую бизнес-логику.
Бизнес-правила должны находиться на backend.
8. FRONTEND STRUCTURE
src/ ├── app/ ├── components/ ├── features/ │ ├── catalog/ │ ├── product/ │ ├── cart/ │ ├── checkout/ │ ├── account/ │ ├── b2b/ │ └── orders/ ├── services/ ├── hooks/ ├── lib/ ├── types/ └── styles/ 
Frontend должен быть организован feature-oriented.
9. BACKEND
Рекомендуемый stack
NestJS + TypeScript
Причины:
модульная архитектура;
dependency injection;
REST API;
validation;
authentication;
testing;
хорошая поддержка enterprise architecture.
Backend должен использовать:
REST API;
OpenAPI;
DTO;
validation;
structured logging;
centralized error handling.
10. DATABASE
Основная БД
PostgreSQL
Используется как основная транзакционная база данных.
Причины:
ACID;
сложные relations;
транзакции;
JSONB;
indexing;
надёжность;
масштабируемость.
11. CACHE
Использовать:
Redis
Основные задачи:
cache;
session;
rate limiting;
temporary cart data;
locks;
idempotency keys;
short-lived data.
Redis не является источником истины для заказов и остатков.
12. SEARCH
Для MVP допускается PostgreSQL Full Text Search.
При увеличении каталога и требований:
OpenSearch / Elasticsearch
Search должен быть отделён от основной transactional database.
13. OBJECT STORAGE
Для:
product images;
videos;
invoices;
documents;
marketing assets.
Использовать S3-compatible Object Storage.
Не хранить большие файлы непосредственно в PostgreSQL.
14. CDN
Все статические assets должны обслуживаться через CDN:
images;
CSS;
JavaScript;
videos;
static files.
Изображения должны автоматически оптимизироваться.
Предпочтительные форматы:
WebP;
AVIF.
15. API GATEWAY
API Gateway должен обеспечивать:
routing;
authentication;
rate limiting;
request logging;
API versioning;
CORS;
security headers.
Основная версия:
/api/v1/
16. ОСНОВНЫЕ BACKEND-МОДУЛИ
Backend должен содержать следующие модули:
Auth Users Customers Companies Catalog Categories Products Variants SKU Pricing Promotions Cart Checkout Orders Payments Inventory Warehouses Shipping Reviews Wishlist B2B Quotes Notifications Countries Currencies Taxes CMS Analytics Integrations Audit Admin
[8/15/2026 1:57 PM] Ada: 17. CATALOG MODULE
Отвечает за:
products;
categories;
variants;
SKU;
attributes;
media;
product status.
Каталог не должен содержать бизнес-логику платежей или заказов.
18. PRODUCT MODEL
Основная структура:
Product │ └── ProductVariant │ └── SKU 
Пример:
MARU Food Container │ ├── 350 ml │ └── SKU-350-TR │ ├── 800 ml │ └── SKU-800-TR │ └── 1000 ml └── SKU-1000-TR 
19. DATABASE MODEL
19.1. Users
Основные поля:
FieldTypeKeyidUUIDPKemailVARCHARUNIQUEphoneVARCHARINDEXpassword_hashVARCHARstatusENUMemail_verifiedBOOLEANphone_verifiedBOOLEANcreated_atTIMESTAMPupdated_atTIMESTAMP 
20. CUSTOMERS
FieldTypeidUUID PKuser_idUUID FKfirst_nameVARCHARlast_nameVARCHARcustomer_typeENUMcountry_idUUID FKcreated_atTIMESTAMPupdated_atTIMESTAMP 
Relationship:
User 1 : 1 Customer
21. COMPANIES
FieldTypeidUUID PKnameVARCHARregistration_numberVARCHARtax_numberVARCHARcountry_idUUID FKaddressTEXTstatusENUMcreated_atTIMESTAMP 
Связь:
Company 1 : N Customers
22. CATEGORIES
FieldTypeidUUID PKparent_idUUID FK nullablenameJSONBslugVARCHAR UNIQUEdescriptionJSONBimage_idUUIDsort_orderINTEGERstatusENUM 
Поддерживается unlimited category depth.
23. PRODUCTS
FieldTypeidUUID PKcategory_idUUID FKnameJSONBslugVARCHAR UNIQUEdescriptionJSONBstatusENUMbrandVARCHARcreated_atTIMESTAMPupdated_atTIMESTAMP 
JSONB используется для multilingual content.
24. PRODUCT VARIANTS
FieldTypeidUUID PKproduct_idUUID FKnameJSONBattributesJSONBstatusENUM 
25. SKU
FieldTypeidUUID PKvariant_idUUID FKskuVARCHAR UNIQUEbarcodeVARCHAR INDEXweightDECIMALlengthDECIMALwidthDECIMALheightDECIMALpackage_quantityINTEGERstatusENUM 
SKU является основной единицей:
продажи;
цены;
склада;
заказа.
26. PRICES
FieldTypeidUUID PKsku_idUUID FKmarket_idUUID FKcustomer_typeENUMcurrency_idUUID FKamountDECIMALmin_quantityINTEGERmax_quantityINTEGER nullablevalid_fromTIMESTAMPvalid_toTIMESTAMP nullable 
27. WAREHOUSES
FieldTypeidUUID PKnameVARCHARcountry_idUUID FKaddressTEXTstatusENUM 
28. INVENTORY
FieldTypeidUUID PKsku_idUUID FKwarehouse_idUUID FKstock_quantityINTEGERreserved_quantityINTEGERupdated_atTIMESTAMP 
Уникальный индекс:
SKU + Warehouse
29. ORDERS
FieldTypeidUUID PKorder_numberVARCHAR UNIQUEcustomer_idUUID FK nullablecompany_idUUID FK nullablecurrency_idUUID FKsubtotalDECIMALdiscount_totalDECIMALshipping_totalDECIMALtax_totalDECIMALgrand_totalDECIMALstatusENUMpayment_statusENUMcreated_atTIMESTAMP 
30. ORDER ITEMS
FieldTypeidUUID PKorder_idUUID FKsku_idUUID FKproduct_name_snapshotJSONBsku_snapshotVARCHARunit_priceDECIMALquantityINTEGERdiscountDECIMALtotalDECIMAL 
Важно:
В заказе необходимо сохранять snapshot названия, SKU и цены.
Изменение товара в будущем не должно менять исторический заказ.
31. PAYMENTS
FieldTypeidUUID PKorder_idUUID FKproviderVARCHARprovider_transaction_idVARCHARamountDECIMALcurrencyVARCHARstatusENUMidempotency_keyVARCHAR UNIQUEpaid_atTIMESTAMP 
32. SHIPMENTS
FieldTypeidUUID PKorder_idUUID FKcarrierVARCHARtracking_numberVARCHARshipping_methodVARCHARstatusENUMestimated_deliveryTIMESTAMPshipped_atTIMESTAMPdelivered_atTIMESTAMP 
33. ADDRESSES
FieldTypeidUUID PKcustomer_idUUID FKcountry_idUUID FKcityVARCHARpostal_codeVARCHARaddress_line1VARCHARaddress_line2VARCHARphoneVARCHAR 
34. DISCOUNTS
Поддерживать:
percentage;
fixed;
quantity;
customer;
market;
product;
category.
35. PROMOCODES
FieldTypeidUUID PKcodeVARCHAR UNIQUEdiscount_idUUID FKvalid_fromTIMESTAMPvalid_toTIMESTAMPusage_limitINTEGERusage_countINTEGERminimum_order_valueDECIMALstatusENUM 
36. REVIEWS
FieldTypeidUUID PKcustomer_idUUID FKproduct_idUUID FKorder_idUUID FKratingSMALLINTcontentTEXTstatusENUMcreated_atTIMESTAMP 
Отзыв желательно разрешать только после покупки соответствующего товара.
37. CARTS
FieldTypeidUUID PKcustomer_idUUID FK nullablesession_idVARCHAR INDEXcurrency_idUUID FKstatusENUMexpires_atTIMESTAMP 
38. WISHLISTS
FieldTypeidUUID PKcustomer_idUUID FKsku_idUUID FKcreated_atTIMESTAMP
[8/15/2026 1:57 PM] Ada: Уникальность:
customer_id + sku_id
39. COUNTRIES
Содержит:
ISO code;
name;
default currency;
timezone;
tax configuration;
shipping availability;
status.
40. CURRENCIES
Содержит:
ISO code;
symbol;
decimal precision;
exchange rate;
status.
41. TAX RULES
FieldTypeidUUID PKcountry_idUUID FKcustomer_typeENUMtax_typeENUMrateDECIMALvalid_fromTIMESTAMPvalid_toTIMESTAMP 
Налоговая логика должна быть конфигурируемой.
42. DATABASE INDEXING
Обязательные индексы:
users.email;
users.phone;
products.slug;
products.status;
SKU.sku;
SKU.barcode;
orders.order_number;
orders.customer_id;
orders.status;
payments.provider_transaction_id;
inventory.sku_id + warehouse_id;
shipments.tracking_number.
Индексы должны регулярно проверяться по фактическим query patterns.
43. API DESIGN
API должен использовать REST.
Base:
/api/v1
Пример:
GET /api/v1/products
GET /api/v1/products/{slug}
POST /api/v1/cart/items
POST /api/v1/checkout
POST /api/v1/orders
44. CATALOG API
GET /products
Parameters:
page;
limit;
category;
price_min;
price_max;
capacity;
color;
availability;
sort;
search.
Response:
{ "data": [], "meta": { "page": 1, "limit": 24, "total": 100 } } 
45. PRODUCT API
GET /products/{slug}
Возвращает:
product;
variants;
SKU;
prices;
availability;
images;
reviews;
related products.
46. CART API
POST /cart/items
Request:
{ "sku_id": "UUID", "quantity": 2 } 
PATCH /cart/items/{id}
Изменяет quantity.
DELETE /cart/items/{id}
Удаляет позицию.
47. CHECKOUT API
POST /checkout
Система:
получает cart;
проверяет цены;
проверяет stock;
рассчитывает discount;
рассчитывает tax;
рассчитывает shipping;
создаёт order;
инициирует payment.
48. ORDER API
GET /orders
История заказов пользователя.
GET /orders/{id}
Детали заказа.
POST /orders/{id}/cancel
Отмена при допустимом статусе.
49. PAYMENT API
POST /payments
Создание payment intent.
POST /payments/webhook
Получение события от payment provider.
Webhook должен быть:
authenticated;
idempotent;
logged.
50. ERROR FORMAT
Все API ошибки должны иметь единый формат:
{ "error": { "code": "PRODUCT_OUT_OF_STOCK", "message": "The selected product is currently unavailable.", "request_id": "UUID" } } 
Не возвращать внутренние stack traces клиенту.
51. PAGINATION
Использовать pagination.
Для обычного каталога допускается:
page + limit
Для больших datasets рекомендуется cursor pagination.
Maximum limit должен быть ограничен.
Например:
limit <= 100
52. FILTERING
API должен поддерживать безопасную фильтрацию.
Пример:
?capacity=1000&availability=in_stock
Нельзя позволять клиенту передавать произвольные SQL expressions.
53. SORTING
Разрешённые значения:
price_asc;
price_desc;
newest;
popularity;
rating.
Необходимо использовать whitelist.
54. AUTHENTICATION
Рекомендуемая схема:
Access Token + Refresh Token
Access token:
короткоживущий.
Refresh token:
долгоживущий и защищённый.
55. REGISTRATION
Пользователь вводит:
email;
phone;
password;
name.
После регистрации:
создаётся User;
создаётся Customer;
отправляется verification;
аккаунт получает статус pending/active согласно политике.
56. PASSWORD SECURITY
Пароли хранить только в виде безопасного password hash.
Никогда не хранить:
plaintext password;
password в логах;
password в analytics.
57. RBAC
Минимальные роли:
CUSTOMER;
B2B_CUSTOMER;
SALES_MANAGER;
PRODUCT_MANAGER;
WAREHOUSE_MANAGER;
ACCOUNTANT;
MARKETING_MANAGER;
ADMIN;
SUPER_ADMIN.
Backend обязан проверять authorization независимо от frontend.
58. ADMIN AUTHENTICATION
Для административной зоны обязательно:
MFA;
strong password policy;
session timeout;
audit log;
role-based access.
59. ORDER ENGINE
Основной pipeline:
Cart ↓ Checkout ↓ Price Validation ↓ Inventory Validation ↓ Order Creation ↓ Inventory Reservation ↓ Payment ↓ Payment Confirmation ↓ Fulfillment ↓ Shipment ↓ Delivery 
60. ORDER STATE MACHINE
NEW ↓ PAYMENT_PENDING ↓ PAID ↓ PROCESSING ↓ PACKED ↓ SHIPPED ↓ DELIVERED
[8/15/2026 1:57 PM] Ada: Альтернативные состояния:
CANCELLED REFUNDED RETURNED PAYMENT_FAILED 
Переходы между статусами должны быть строго контролируемыми.
61. IDEMPOTENCY
Критические операции должны быть idempotent:
create order;
payment;
payment webhook;
refund;
inventory reservation.
Если клиент повторяет запрос из-за timeout, не должен создаваться второй заказ или второй payment.
62. INVENTORY ENGINE
Основные показатели:
Stock Reserved Available Sold 
Формула:
Available = Stock − Reserved
63. RESERVATION
При подтверждении заказа:
Stock = 100 Reserved = 0 Available = 100 
После reservation 5:
Stock = 100 Reserved = 5 Available = 95 
После продажи:
Stock = 95 Reserved = 0 Available = 95 
64. RACE CONDITIONS
Одновременные заказы одного SKU не должны приводить к отрицательному stock.
Использовать:
database transaction;
row-level locking;
atomic update;
reservation logic.
65. OVERSELLING
Backend должен отказать в reservation, если:
Available < Requested Quantity
Frontend получает:
INSUFFICIENT_STOCK
и предлагает уменьшить количество.
66. CANCELLATION
При отмене:
Reserved → Available
Reservation снимается.
67. REFUND
При refund:
payment status → refunded;
order status → refunded/returned;
inventory корректируется согласно правилам возврата;
создаётся audit record.
68. MULTIPLE WAREHOUSES
Алгоритм выбора склада может учитывать:
наличие;
страну клиента;
стоимость доставки;
расстояние;
приоритет склада.
На первом этапе допускается ручная настройка приоритета.
69. PRICING ENGINE
Расчёт:
Base Price ↓ Market Price ↓ Customer Price ↓ Quantity Discount ↓ Promotion ↓ Promo Code ↓ Tax ↓ Shipping ↓ Final Total 
70. PRICE SNAPSHOT
После создания заказа сохраняются:
unit price;
discount;
tax;
shipping;
final price.
Последующее изменение прайса не меняет существующий заказ.
71. INTERNATIONALIZATION
Поддержать:
RU;
UZ;
EN.
Архитектура должна позволять добавить новые языки без изменения database schema.
72. LOCALE
Locale определяет:
language;
date format;
number format;
currency;
timezone.
Например:
uz-UZ
ru-UZ
en-US
73. CURRENCY
Цена должна быть привязана к currency.
Нельзя считать, что:
1 = 1
между валютами.
Курсы валют должны иметь timestamp.
Исторические заказы используют сохранённую валюту и сумму.
74. TAX
Tax Engine должен принимать:
country;
region;
customer type;
product;
order value.
Расчёт должен происходить на backend.
Frontend только отображает результат.
75. TIMEZONE
Все timestamps в database рекомендуется хранить в UTC.
Frontend отображает дату в timezone пользователя/рынка.
76. SECURITY ARCHITECTURE
Основываться на:
OWASP principles;
least privilege;
defense in depth;
secure defaults.
77. HTTPS
В production весь traffic должен использовать HTTPS.
HTTP должен перенаправляться на HTTPS.
78. DATA ENCRYPTION
Защищать:
passwords;
secrets;
sensitive personal information;
credentials.
Encryption at rest должен использоваться для инфраструктуры, где это поддерживается.
79. SECRETS
API keys, database passwords и credentials нельзя хранить:
в Git;
в frontend;
в исходном коде.
Использовать secret management.
80. RATE LIMITING
Ограничивать:
login;
registration;
password reset;
checkout;
payment;
public API;
search.
Особенно защищать authentication endpoints.
81. AUDIT LOG
Записывать:
user;
action;
entity;
entity_id;
old value;
new value;
timestamp;
IP;
request_id.
Особенно:
изменение цены;
изменение остатка;
refund;
cancellation;
admin actions.
82. BACKUP
Минимум:
automated daily backup;
point-in-time recovery для production database;
off-site backup;
backup monitoring.
Backup считается существующим только после проверки возможности восстановления.
83. DISASTER RECOVERY
Определить:
RPO
целевую потерю данных.
RTO
целевое время восстановления.
Для production значения должны быть утверждены перед запуском.
84. PERFORMANCE TARGETS
Целевые показатели:
API
Для обычных запросов:
[8/15/2026 1:57 PM] Ada: p95 < 300 ms
при штатной нагрузке.
Database
Большинство обычных queries:
<100 ms
Checkout
Основные серверные операции должны выполняться без необоснованных задержек.
85. FRONTEND PERFORMANCE
Цели:
optimized images;
lazy loading;
code splitting;
caching;
CDN;
minimized JavaScript;
SSR/streaming где это полезно.
Особое внимание:
Product Page и Checkout.
86. IMAGE OPTIMIZATION
Original image хранится в Object Storage.
Для frontend генерируются:
thumbnail;
mobile;
desktop;
retina;
WebP;
AVIF при поддержке.
87. CACHING STRATEGY
Кэшировать:
categories;
product data;
recommendations;
configuration;
country data;
currency data.
Не кэшировать без специальной стратегии:
payment status;
inventory critical state;
personal order information.
88. ASYNCHRONOUS PROCESSING
Для фоновых задач использовать queue/worker architecture.
Например:
Order ↓ Queue ├── Email ├── CRM ├── ERP ├── Analytics └── Notification 
Основной checkout не должен ждать завершения всех внешних интеграций.
89. MESSAGE QUEUE
Для MVP можно использовать Redis-based queue.
При масштабировании допускается переход на:
RabbitMQ;
Kafka;
managed queue service.
90. EXTERNAL INTEGRATIONS
Интеграции не должны находиться непосредственно внутри Order Controller.
Использовать adapter pattern:
Order Module │ Integration Interface │ ┌───┼────┬────┐ ERP CRM Payment Shipping 
Это позволит заменить внешнего поставщика без изменения основной бизнес-логики.
91. LOGGING
Использовать structured JSON logs.
Каждый request должен иметь:
request_id
Ошибки должны связываться с:
user;
order;
payment;
request.
92. MONITORING
Отслеживать:
CPU;
RAM;
database;
API latency;
errors;
queue;
payment failures;
inventory errors;
integration failures.
93. ALERTING
Критические alerts:
database unavailable;
payment failures above threshold;
API error rate;
inventory synchronization failure;
ERP synchronization failure;
queue backlog;
storage failure.
94. DEVOPS ENVIRONMENTS
Минимум:
Development ↓ Testing ↓ Staging ↓ Production 
Production не должен использоваться для разработки.
95. GIT
Использовать Git.
Рекомендуемый workflow:
feature/* ↓ Pull Request ↓ Code Review ↓ Automated Tests ↓ Merge ↓ Staging ↓ Production 
96. CI/CD
Pipeline:
Commit ↓ Lint ↓ Unit Tests ↓ Build ↓ Security Scan ↓ Integration Tests ↓ Deploy Staging ↓ E2E Tests ↓ Approval ↓ Production 
97. TESTING
Минимально:
Unit Tests
Business logic.
Integration Tests
Database/API/integrations.
E2E
Ключевые пользовательские сценарии.
Load Tests
Checkout, catalog, search.
Security Tests
Authentication/API/security.
98. КРИТИЧЕСКИЕ E2E СЦЕНАРИИ
Обязательно протестировать:
Guest purchase.
Registered purchase.
Failed payment.
Successful payment.
Duplicate payment webhook.
Out-of-stock.
Cart price change.
Coupon.
Quantity discount.
Order cancellation.
Refund.
International order.
B2B quote.
Multiple warehouse.
CRM failure.
ERP failure.
99. DEPLOYMENT
Production deployment должен поддерживать:
zero/minimal downtime;
rollback;
versioned releases;
database migration control.
100. DATABASE MIGRATIONS
Все изменения схемы БД должны выполняться через version-controlled migrations.
Нельзя вручную менять production schema без documented migration.
101. API VERSIONING
Использовать:
/api/v1
При breaking changes:
/api/v2
Старые версии не удалять немедленно.
Должен существовать migration/deprecation policy.
102. GDPR / PRIVACY ARCHITECTURE
Для международных рынков необходимо предусмотреть архитектурную возможность:
consent;
data deletion;
data export;
privacy settings;
cookie management.
Конкретные юридические требования должны быть отдельно подтверждены юристами для соответствующего рынка.
103. PERSONAL DATA
PII должна быть минимизирована.
Доступ к PII получают только роли, которым это необходимо.
104. ADMIN ARCHITECTURE
Admin UI использует тот же backend API, но с отдельными authorization policies.
[8/15/2026 1:57 PM] Ada: Admin не должен получать права только на основании frontend route.
Backend проверяет RBAC на каждом защищённом endpoint.
105. ANALYTICS
Analytics events отправляются через отдельный analytics layer.
Основные события:
view_product;
search;
add_to_cart;
begin_checkout;
payment;
purchase;
request_quote;
signup;
wishlist.
Не передавать чувствительные данные в рекламные analytics системы.
106. OBSERVABILITY
Три основных слоя:
Logs
Что произошло.
Metrics
Насколько часто произошло.
Traces
Где именно возникла задержка/ошибка.
107. SCALABILITY
Первоначальная архитектура должна масштабироваться горизонтально:
Load Balancer │ ┌────────┼────────┐ ▼ ▼ ▼ App 1 App 2 App 3 │ │ │ └────────┼────────┘ ▼ PostgreSQL 
Application layer должен быть stateless.
108. FUTURE MICROSERVICE EXTRACTION
При росте MARU можно выделить:
Commerce Core │ ┌────┼───────┬─────────┐ ▼ ▼ ▼ ▼ Search Payment Shipping Notifications 
Позже:
Marketplace Service;
Analytics Service;
Recommendation Service.
109. NON-FUNCTIONAL REQUIREMENTS
Система должна обеспечивать:
availability;
performance;
security;
scalability;
maintainability;
observability;
recoverability;
testability.
110. ACCEPTANCE CRITERIA — ARCHITECTURE
Архитектура считается принятой, если:
frontend отделён от backend;
backend разделён на модули;
PostgreSQL является source of truth;
Redis не используется как основная БД;
API имеет versioning;
API документирован через OpenAPI;
authentication реализована безопасно;
RBAC работает на backend;
платежи idempotent;
inventory защищён от overselling;
order state machine реализована;
цены сохраняются snapshot;
поддерживаются multiple warehouses;
поддерживаются currencies;
поддерживаются languages;
предусмотрены taxes;
предусмотрены backups;
настроены monitoring и logging;
есть CI/CD;
есть staging;
предусмотрен rollback;
критические сценарии покрыты автоматическими тестами.
111. ACCEPTANCE CRITERIA — ORDER
Тест:
100 единиц SKU на складе.
Одновременно поступают два заказа:
Order A — 70;
Order B — 50.
Система должна:
подтвердить reservation первого заказа;
не допустить продажи сверх доступного остатка;
корректно отклонить или частично обработать второй заказ согласно бизнес-правилам;
не получить отрицательный inventory;
сохранить audit trail.
112. ACCEPTANCE CRITERIA — PAYMENT
При повторной отправке одного и того же payment webhook:
не должен создаваться второй payment или второй заказ.
113. ACCEPTANCE CRITERIA — PRICE
Если товар стоил:
$10
и заказ оформлен по этой цене, после изменения цены на:
$12
исторический заказ продолжает отображать:
$10.
114. ACCEPTANCE CRITERIA — INTEGRATION FAILURE
Если ERP временно недоступна:
заказ не должен теряться;
пользователь не должен получать ложное сообщение об отмене;
событие должно попасть в queue;
должна выполняться retry policy;
ошибка должна попасть в monitoring.
115. ACCEPTANCE CRITERIA — SECURITY
Нельзя:
получить чужой заказ по изменению ID;
получить admin endpoint без соответствующей роли;
выполнить payment без authorization;
получить полный customer data через публичный API;
передать произвольный SQL filter.
116. РЕКОМЕНДУЕМЫЙ TECH STACK
LayerTechnologyFrontendNext.js / React / TypeScriptBackendNestJS / TypeScriptDatabasePostgreSQLCacheRedisSearchPostgreSQL FTS → OpenSearchStorageS3-compatibleCDNCloud CDNAPIREST / OpenAPIQueueRedis Queue → managed queue/RabbitMQ при ростеAuthenticationAccess + Refresh TokenMonitoringPrometheus/Grafana или managed equivalentError TrackingSentry или аналогCI/CDGitHub Actions/GitLab CIContainersDockerReverse ProxyNginx/managed load balancerInfrastructureCloud/VPS на первом этапе 
117. INFRASTRUCTURE STRATEGY
Не рекомендуется с первого дня создавать дорогостоящую Kubernetes-инфраструктуру.
Для MVP достаточно:
CDN ↓ Load Balancer ↓ Application ↓ PostgreSQL ↓ Redis ↓ Object Storage 
Docker должен использоваться с самого начала, чтобы облегчить дальнейшую миграцию инфраструктуры.
[8/15/2026 1:57 PM] Ada: Kubernetes рассматривать после появления реальной потребности.
118. MASTER DATA PRINCIPLE
Для каждой категории данных должен быть определён Master System.
Пример:
DataMasterProductERP/CommerceSKUERP/CommerceInventoryERPOrderCommercePaymentPayment Provider + CommerceCustomerCRM/CommerceAccountingERPMarketing AnalyticsAnalytics Platform 
Окончательная матрица Master Data должна быть утверждена до разработки интеграций.
119. ГЛАВНЫЙ АРХИТЕКТУРНЫЙ ПРИНЦИП MARU
Система должна строиться не вокруг веб-сайта, а вокруг Commerce Core.
MARU COMMERCE CORE │ ┌────────────────┼─────────────────┐ │ │ │ Website Marketplace B2B │ │ │ └────────────────┼─────────────────┘ │ Orders / Customers │ ┌──────────┴──────────┐ ▼ ▼ ERP CRM │ ▼ Warehouse │ ▼ Shipping 
Это позволит в будущем заменить Website, добавить мобильное приложение или подключить новый marketplace, не переписывая ядро торговли.
120. ИТОГ
ТЗ №3 определяет технический фундамент MARU E-commerce.
Архитектура должна стартовать как:
Modular Monolith + API-first
с:
Next.js;
NestJS;
PostgreSQL;
Redis;
Object Storage;
CDN;
Queue;
Docker;
CI/CD;
Monitoring;
Security Layer.
При росте бизнеса отдельные модули могут быть вынесены в microservices.
Ключевая архитектурная цепочка:
Frontend → API → Commerce Core → PostgreSQL/Redis → Queue → ERP/CRM/Payment/Shipping
При этом критические данные — заказы, цены, платежи и остатки — должны обрабатываться транзакционно и иметь однозначный источник истины.
ТЗ №3 является техническим основанием для проектирования backend, frontend-инфраструктуры, базы данных, API, DevOps и последующей разработки ТЗ №4 по внешним интеграциям.
ТЗ №4 — ИНТЕГРАЦИИ MARU E-COMMERCE
Проект: MARU E-commerce
Документ: Integration Architecture & Integration Specification
Версия: 1.0
Основание: ТЗ №1, №2, №3
Назначение: Integration Architect, Backend Developer, 1С Developer, CRM Developer, DevOps, QA
1. ЦЕЛЬ
Создать единую интеграционную архитектуру MARU E-commerce, обеспечивающую обмен данными между интернет-магазином и внешними системами:
ERP / 1С;
CRM;
платежными системами;
службами доставки;
marketplace;
SMS;
Email;
WhatsApp;
Telegram;
Google Analytics;
Google Tag Manager;
Meta;
другими будущими сервисами.
Главный принцип:
Внешняя система не должна напрямую изменять внутреннюю бизнес-логику MARU Commerce Core.
Все интеграции выполняются через Integration Layer / Adapter.
2. ОБЩАЯ АРХИТЕКТУРА
                    MARU WEBSITE
                         │
                         ▼
                 MARU COMMERCE CORE
                         │
                         ▼
                  INTEGRATION LAYER
                         │
       ┌─────────────────┼──────────────────┐
       │                 │                  │
       ▼                 ▼                  ▼
      ERP               CRM              Payment
       │                 │                  │
       ▼                 ▼                  ▼
    Warehouse          Sales           Provider
       │
       ▼
    Shipping

       ┌─────────────────────────────────────┐
       │                                     │
       ▼                                     ▼
 Marketplace                         Notifications
 Connectors                         SMS / Email / WA
       │
       ▼
 UZ / International

       ┌─────────────────────────────────────┐
       ▼
 Analytics / Tracking
3. ГЛАВНЫЙ ПРИНЦИП — ADAPTER ARCHITECTURE
Каждая внешняя система подключается через стандартный интерфейс.
Например:
PaymentService
      │
      ▼
PaymentProviderAdapter
      │
 ┌────┼─────────────┐
 ▼    ▼             ▼
Local International Future
Provider Provider    Provider
Commerce Core не должен знать внутренний API конкретного payment provider.
То же самое применяется к:
ERP;
CRM;
Shipping;
Marketplace;
Notification.
4. INTEGRATION MODULES
Создать следующие модули:
[8/15/2026 1:57 PM] Ada: Integrations
│
├── ERP
├── CRM
├── Payment
├── Shipping
├── Marketplace
├── Email
├── SMS
├── WhatsApp
├── Telegram
├── Analytics
└── Webhooks
5. MASTER SYSTEM MATRIX
До подключения каждой системы необходимо определить владельца данных.
Базовая матрица:
Данные
Master System
Product
MARU Commerce / ERP
SKU
ERP / Commerce
Product description
Commerce
Price
ERP / Commerce
Inventory
ERP
Warehouse
ERP
Customer
Commerce / CRM
B2B Lead
CRM
Order
Commerce
Payment
Payment Provider + Commerce
Accounting
ERP
Shipment
Shipping Provider
Tracking
Shipping Provider
Marketing attribution
Analytics
Marketplace order
Commerce после импорта
Финальная матрица утверждается до начала разработки интеграций.
6. ERP / 1С
6.1. Назначение
Интеграция должна обеспечивать обмен:
товарами;
SKU;
ценами;
остатками;
складами;
клиентами;
заказами;
оплатами;
возвратами;
документами.
7. ERP → WEBSITE
Из ERP могут передаваться:
Products
SKU;
barcode;
product name;
attributes;
weight;
dimensions;
status.
Prices
base price;
wholesale price;
customer price;
market price.
Inventory
warehouse;
stock;
reserved;
available.
Documents
invoice;
fiscal document;
shipment document.
8. WEBSITE → ERP
Website передает:
customer;
company;
order;
order items;
price;
discount;
shipping;
payment;
delivery;
cancellation;
refund.
9. ERP SYNC MODEL
Для критических данных использовать комбинацию:
Real-time + scheduled synchronization.
Например:
Stock
Real-time / near real-time.
Order
Real-time.
Product catalog
Batch + manual synchronization.
Prices
Batch + event-based при возможности.
10. ERP ORDER FLOW
Website
   │
   ▼
Order Created
   │
   ▼
Integration Queue
   │
   ▼
ERP Adapter
   │
   ▼
ERP
   │
   ▼
ERP Order ID
   │
   ▼
MARU Order
ERP ID должен сохраняться в MARU:
order.erp_order_id
11. ERP ID MAPPING
Необходимо создать таблицу соответствий:
MARU ID
ERP ID
Entity Type
External System
Created At
Updated At
Например:
MARU SKU: SKU-1000-001
ERP SKU: 000000145
12. ERP DUPLICATE PROTECTION
Повторная отправка одного заказа не должна создать второй ERP order.
Использовать:
external_id;
idempotency key;
mapping table.
13. ERP RETRY
Если ERP недоступна:
Attempt 1
   ↓
Retry
   ↓
Retry
   ↓
Retry
   ↓
Dead Letter Queue
Количество retry и интервалы должны быть configurable.
14. CRM INTEGRATION
CRM получает:
leads;
customers;
companies;
orders;
B2B requests;
Request Quote;
source;
campaign;
UTM;
manager assignment.
15. LEAD FLOW
Website
 ↓
Lead
 ↓
CRM Adapter
 ↓
CRM
Передавать:
name;
email;
phone;
company;
country;
source;
campaign;
requested products;
quantity;
message.
16. REQUEST QUOTE
Особенно важный B2B сценарий:
B2B Customer
      ↓
Request Quote
      ↓
MARU Commerce
      ↓
CRM
      ↓
Sales Manager
      ↓
Offer
      ↓
Customer
      ↓
Order
Request Quote должен иметь собственный ID.
Например:
RFQ-2026-000123
17. CRM ORDER SYNCHRONIZATION
После создания заказа:
Order Created
      ↓
CRM
CRM получает:
order number;
customer;
company;
amount;
currency;
products;
source;
status.
18. MARKETING ATTRIBUTION
Передавать:
UTM source;
UTM medium;
UTM campaign;
UTM content;
UTM term;
landing page;
referral;
click identifiers, если применимо.
Источник должен сохраняться в customer/order context.
19. PAYMENT ARCHITECTURE
Не привязывать Commerce Core к конкретному payment provider.
Использовать:
Commerce Core
      ↓
Payment Interface
      ↓
Payment Adapter
      ↓
Provider
20. PAYMENT INTERFACE
Минимальные операции:
createPayment()
getPaymentStatus()
cancelPayment()
refundPayment()
verifyWebhook()
21. PAYMENT PROVIDER TYPES
Система должна поддерживать:
Local Provider
Для локальных платежей.
International Provider
Для международных карт/платежей.
Future Provider
Добавляется без изменения Order Engine.
22. PAYMENT FLOW
Customer
 ↓
Checkout
 ↓
Create Order
 ↓
Create Payment
 ↓
Payment Provider
[8/15/2026 1:57 PM] Ada: ↓
Customer Payment
 ↓
Webhook
 ↓
Payment Adapter
 ↓
Commerce Core
 ↓
Order = PAID
23. PAYMENT STATUS
Минимально:
CREATED
PENDING
AUTHORIZED
PAID
FAILED
CANCELLED
REFUNDED
PARTIALLY_REFUNDED
24. PAYMENT WEBHOOK
Endpoint:
POST /api/v1/integrations/payments/{provider}/webhook
Webhook должен:
проверить подпись;
определить provider;
определить transaction;
проверить idempotency;
обновить payment;
обновить order;
записать audit;
вернуть success.
25. PAYMENT DUPLICATION
Один transaction ID не может быть обработан дважды.
Обязательный unique index:
provider + provider_transaction_id
26. PAYMENT RECONCILIATION
Система должна периодически сравнивать:
MARU Payments
       ↕
Provider Payments
Выявлять:
missing payment;
duplicate;
amount mismatch;
currency mismatch;
status mismatch.
27. PAYMENT FAILURE
Если provider вернул ошибку:
payment = FAILED;
order не должен автоматически считаться PAID;
inventory reservation обрабатывается согласно TTL;
пользователь получает возможность повторить оплату.
28. REFUND
Order
 ↓
Refund Request
 ↓
Payment Adapter
 ↓
Provider
 ↓
Webhook/Response
 ↓
Payment = REFUNDED
 ↓
Order = REFUNDED
29. SHIPPING ARCHITECTURE
Использовать:
ShippingService
      ↓
ShippingProviderAdapter
      ↓
Provider
Поддержать:
local delivery;
courier;
freight;
international courier;
pickup;
future providers.
30. SHIPPING FUNCTIONS
Adapter должен поддерживать:
getRates()
createShipment()
cancelShipment()
getTracking()
getDeliveryEstimate()
31. SHIPPING FLOW
Order
 ↓
Shipping Rate
 ↓
Customer Selects Delivery
 ↓
Order
 ↓
Create Shipment
 ↓
Tracking Number
 ↓
Shipment
 ↓
Tracking Updates
 ↓
Delivered
32. SHIPPING DATA
Передавать:
order number;
recipient;
phone;
address;
country;
postal code;
package dimensions;
weight;
quantity;
declared value;
delivery type.
33. INTERNATIONAL SHIPPING
Система должна учитывать:
destination country;
shipping method;
weight;
dimensions;
customs requirements;
declared value;
delivery estimate.
Конкретные таможенные правила должны конфигурироваться отдельно.
34. MARKETPLACE ARCHITECTURE
Основной принцип:
Central Product Catalog → Marketplace Connectors
                  MARU Catalog
                       │
              Marketplace Layer
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
     Uzum          Local MP       International MP
35. MARKETPLACE CONNECTOR
Каждый connector должен реализовать стандартный interface:
publishProduct()
updateProduct()
updatePrice()
updateStock()
getOrders()
updateOrderStatus()
getReturns()
36. UZUM
Uzum должен подключаться как отдельный connector.
Необходимо поддержать:
products;
SKU;
prices;
stock;
orders;
order status;
returns;
shipment data.
Конкретные endpoint и authentication определяются официальной документацией API Uzum на момент подключения.
37. ДРУГИЕ MARKETPLACE
Добавление нового marketplace должно выглядеть:
MarketplaceConnector
       │
       ├── UzumConnector
       ├── LocalMarketplaceConnector
       ├── InternationalMarketplaceConnector
       └── FutureConnector
Без изменения Product, Order и Inventory modules.
38. MARKETPLACE STOCK
Stock должен контролироваться Commerce/ERP.
Marketplace не должен становиться самостоятельным Master System для MARU inventory.
39. MARKETPLACE ORDER
Marketplace
 ↓
Connector
 ↓
MARU Order Adapter
 ↓
Commerce Order
 ↓
ERP
Marketplace order ID сохраняется.
40. SMS
Создать универсальный:
SmsProviderAdapter
Функции:
send()
getStatus()
Использование:
OTP;
order confirmation;
shipment;
delivery;
password reset.
41. EMAIL
Использовать:
EmailProviderAdapter
Типы:
transactional;
marketing.
Transactional email:
registration;
verification;
password reset;
order;
payment;
shipment;
delivery;
refund.
Marketing email должен иметь отдельный consent mechanism.
42. NOTIFICATION TEMPLATE
[8/15/2026 1:57 PM] Ada: Шаблоны не должны быть hardcoded внутри backend.
Структура:
Template
Language
Event
Subject
Body
Status
Поддерживать:
RU;
UZ;
EN.
43. WHATSAPP
Предусмотреть:
WhatsAppProviderAdapter
Возможные события:
order confirmation;
payment;
shipment;
delivery;
sales communication;
B2B communication.
Не делать WhatsApp обязательным компонентом checkout.
44. TELEGRAM
Предусмотреть Telegram integration.
Возможности:
notifications;
support;
order status;
sales communication;
admin notifications.
45. ANALYTICS ARCHITECTURE
Website
  │
  ├── GTM
  ├── GA4
  ├── Meta
  │
  └── Server-side Events
          │
          ▼
      Analytics
46. GA4 EVENTS
Минимальный набор:
view_item
view_item_list
search
add_to_cart
remove_from_cart
view_cart
begin_checkout
add_payment_info
purchase
refund
sign_up
login
add_to_wishlist
generate_lead
47. GTM
Google Tag Manager используется для управления tracking configuration без необходимости менять frontend при каждом marketing tag update.
Но критические ecommerce events должны иметь контролируемый data layer.
48. META
Поддержать:
browser Pixel;
Conversion API / server-side tracking при необходимости.
Ключевые события:
ViewContent;
AddToCart;
InitiateCheckout;
Purchase;
Lead.
49. SERVER-SIDE TRACKING
Для критических conversion events рекомендуется предусмотреть возможность server-side отправки.
Например:
Order Paid
     ↓
Analytics Event
     ↓
Server
     ↓
Analytics / Advertising Platform
Это снижает зависимость от browser-only tracking.
50. WEBHOOK ARCHITECTURE
Все внешние webhooks должны проходить:
External Provider
       ↓
Webhook Endpoint
       ↓
Authentication
       ↓
Signature Verification
       ↓
Idempotency
       ↓
Queue
       ↓
Handler
       ↓
Commerce Core
51. WEBHOOK SECURITY
Для каждого provider использовать, если поддерживается:
HMAC;
signature;
secret;
timestamp verification;
IP allowlist при необходимости.
Нельзя доверять webhook только потому, что запрос пришёл на правильный URL.
52. RETRY POLICY
Retry применяется для временных ошибок:
HTTP 408;
HTTP 429;
HTTP 500;
HTTP 502;
HTTP 503;
network timeout.
Не следует автоматически повторять бизнес-ошибки:
invalid customer;
invalid SKU;
insufficient stock;
invalid payment.
53. EXPONENTIAL BACKOFF
Рекомендуемая схема:
Attempt 1 → 1 min
Attempt 2 → 5 min
Attempt 3 → 15 min
Attempt 4 → 30 min
Attempt 5 → 60 min
Конкретные значения должны быть configurable.
54. DEAD LETTER QUEUE
После исчерпания retry:
Failed Message
      ↓
Dead Letter Queue
      ↓
Admin Alert
      ↓
Manual Retry
55. TIMEOUTS
Для внешних API обязательно устанавливать timeout.
Нельзя допускать бесконечного ожидания provider.
Рекомендуемый initial range:
5–15 секунд в зависимости от операции.
56. LOGGING
Каждая интеграция должна записывать:
request_id;
integration;
provider;
operation;
timestamp;
duration;
status;
error code;
external ID;
internal ID.
Sensitive data должна маскироваться.
57. INTEGRATION LOG
Создать отдельную сущность:
IntegrationLog
Поля:
id
integration
operation
direction
internal_entity
internal_id
external_id
request_id
status
error_code
attempt
created_at
completed_at
58. SYNCHRONIZATION JOBS
Для batch synchronization использовать scheduled jobs.
Например:
Every 5 min:
Stock synchronization

Every 15 min:
Price synchronization

Every 30 min:
Product synchronization

Daily:
Reconciliation
Фактические интервалы должны быть configurable.
59. CONFLICT RESOLUTION
Если две системы изменили один объект:
определить Master System;
Master System имеет приоритет;
конфликт записать в Integration Log;
уведомить ответственного;
автоматически исправить вторичную систему, если возможно.
60. STOCK CONFLICT
Если:
ERP = 100
Website = 90
ERP является Master.
Website должен получить:
100
если иное не предусмотрено утвержденной бизнес-логикой reservation.
61. PRICE CONFLICT
Если ERP является Master Price:
[8/15/2026 1:57 PM] Ada: ERP Price → Commerce Price
Ручное изменение цены на Website запрещается или допускается только через специальный override mechanism.
62. CUSTOMER DUPLICATES
Для поиска duplicate customer использовать:
verified email;
verified phone;
CRM ID;
ERP ID.
Не создавать нового клиента при каждом повторном заказе.
63. ORDER DUPLICATES
Основной ключ:
MARU Order ID
Дополнительно:
External Order ID
Уникальность должна контролироваться database constraints.
64. API AUTHENTICATION
В зависимости от provider:
OAuth2;
API key;
HMAC;
Basic Auth только если provider требует и соединение защищено;
signed JWT;
mTLS для enterprise integrations при необходимости.
Credentials хранятся только в secrets management.
65. INTEGRATION HEALTH
Каждая интеграция должна иметь health status:
HEALTHY
DEGRADED
FAILED
DISABLED
66. MONITORING DASHBOARD
Dashboard должен показывать:
successful calls;
failed calls;
latency;
retry count;
queue size;
webhook failures;
synchronization lag.
67. CRITICAL ALERTS
Создать alerts для:
ERP
stock sync failure;
order sync failure.
Payment
payment failure spike;
webhook failure;
reconciliation mismatch.
Shipping
shipment creation failure;
tracking synchronization failure.
Marketplace
product sync failure;
stock mismatch;
order import failure.
68. STOCK MISMATCH MONITORING
Ежедневно/периодически сравнивать:
ERP Stock
Commerce Stock
Marketplace Stock
Результат:
MATCH
MISMATCH
UNKNOWN
При mismatch создаётся alert.
69. ORDER RECONCILIATION
Периодически сравнивать:
Website Orders
ERP Orders
Marketplace Orders
Payment Transactions
Система должна находить:
missing order;
duplicate;
wrong amount;
missing payment;
status mismatch.
70. API DOCUMENTATION
Каждая интеграция должна иметь OpenAPI/technical documentation:
endpoint;
method;
auth;
headers;
request;
response;
error;
webhook;
retry;
timeout;
idempotency.
71. INTERNAL INTEGRATION CONTRACT
MARU должен иметь собственные стабильные interfaces.
Например:
interface PaymentProviderAdapter {
  createPayment(): Promise<Payment>;
  getPaymentStatus(): Promise<PaymentStatus>;
  refundPayment(): Promise<Refund>;
  verifyWebhook(): Promise<boolean>;
}
Фактическая реализация каждого provider скрыта внутри adapter.
72. ERP ADAPTER
interface ERPAdapter {
  syncProducts();
  syncPrices();
  syncInventory();
  createOrder();
  updateOrder();
  syncCustomers();
  syncPayments();
  syncReturns();
}
73. SHIPPING ADAPTER
interface ShippingAdapter {
  getRates();
  createShipment();
  cancelShipment();
  getTracking();
}
74. MARKETPLACE ADAPTER
interface MarketplaceAdapter {
  publishProduct();
  updateProduct();
  updatePrice();
  updateInventory();
  getOrders();
  updateOrderStatus();
  getReturns();
}
75. NOTIFICATION ADAPTER
interface NotificationAdapter {
  send();
  getStatus();
}
76. INTEGRATION EVENT MODEL
Внутренние события:
ProductUpdated
PriceUpdated
InventoryUpdated
CustomerCreated
OrderCreated
OrderPaid
OrderCancelled
RefundCreated
ShipmentCreated
ShipmentDelivered
QuoteCreated
Эти события могут запускать внешние интеграции.
77. EVENT FLOW EXAMPLE
После оплаты:
PaymentConfirmed
       │
       ├── ERP
       ├── CRM
       ├── Email
       ├── SMS
       ├── Analytics
       └── Marketing
Если один внешний сервис недоступен, остальные не должны автоматически падать.
78. INTEGRATION FAILURE ISOLATION
Например:
CRM недоступна.
Это не должно блокировать:
payment;
order creation;
inventory;
shipment.
CRM event помещается в queue и отправляется позже.
79. DATA TRANSFORMATION
Для каждой интеграции создать mapping:
MARU Field
      ↓
Transformation
      ↓
External Field
Например:
MARU:
sku

ERP:
Номенклатура.Код
Mapping должен быть документирован.
80. DATA NORMALIZATION
Внутри Commerce Core данные должны храниться в едином формате.
Например:
currency → ISO 4217;
country → ISO 3166;
language → ISO 639;
[8/15/2026 1:57 PM] Ada: phone → E.164, где применимо;
timestamps → UTC.
81. DOCUMENT SYNCHRONIZATION
Если ERP создаёт:
invoice;
fiscal receipt;
shipping document;
return document,
Commerce должен получать:
document ID;
type;
URL/file reference;
status;
created date.
82. FILE INTEGRATION
Документы не следует передавать через database.
Использовать:
ERP
 ↓
Integration
 ↓
Object Storage
 ↓
Commerce
При необходимости пользователю выдаётся signed URL.
83. SECURITY OF DOCUMENTS
Документы клиентов должны быть:
private;
access-controlled;
not publicly indexed;
protected from unauthorized download.
84. B2B INTEGRATION
B2B workflow:
B2B Customer
 ↓
Request Quote
 ↓
CRM
 ↓
Sales Manager
 ↓
Quote
 ↓
Commerce
 ↓
Order
 ↓
ERP
Quote должен хранить:
customer;
company;
products;
quantity;
requested price;
proposed price;
currency;
validity;
payment terms;
delivery terms.
85. QUOTE → ORDER
После принятия quote:
Quote ACCEPTED
      ↓
Order CREATED
Цена quote должна быть snapshot.
Изменение общего price list не должно менять accepted quote.
86. LOCAL MARKET
Для Узбекистана архитектура должна позволять подключить:
локальные платежи;
локальную доставку;
SMS;
локальные marketplace;
1С/ERP;
CRM.
Но конкретные provider implementations подключаются только после выбора поставщика.
87. INTERNATIONAL MARKET
Для международных рынков предусмотреть:
international payment;
international shipping;
currency conversion;
country-specific tax;
tracking;
multilingual notifications;
customs data.
88. API RATE LIMITING
Каждый внешний provider может иметь собственный API limit.
Adapter должен поддерживать:
rate limit;
queue;
backoff;
retry.
89. IDEMPOTENCY
Все следующие операции должны иметь idempotency:
create order;
create payment;
refund;
shipment;
marketplace order import.
90. VERSIONING
External adapters должны поддерживать version:
PaymentProviderV1
PaymentProviderV2
Это позволяет менять API provider без переписывания Commerce Core.
91. TEST ENVIRONMENTS
Для каждой интеграции желательно иметь:
Sandbox;
Test credentials;
Production credentials.
Production credentials запрещено использовать в development.
92. TEST DATA
Тестовые данные не должны содержать реальные:
customer PII;
payment cards;
production credentials;
commercial secrets.
93. INTEGRATION TEST MATRIX
Integration
Test
ERP
Product sync
ERP
Price sync
ERP
Stock sync
ERP
Order export
ERP
Return
CRM
Lead
CRM
Customer
CRM
RFQ
Payment
Success
Payment
Failure
Payment
Duplicate webhook
Payment
Refund
Shipping
Rate
Shipping
Shipment
Shipping
Tracking
Marketplace
Product
Marketplace
Stock
Marketplace
Order
SMS
OTP
Email
Order
Analytics
Purchase
94. ACCEPTANCE TEST — ERP
Scenario
Создать товар в ERP.
Expected:
товар попадает в synchronization queue;
Commerce получает SKU;
SKU создаётся/обновляется;
duplicate не создаётся;
Integration Log содержит успешный результат.
95. ACCEPTANCE TEST — STOCK
ERP:
100 шт.
Commerce:
100 шт.
ERP меняет:
80 шт.
Expected:
Commerce:
80 шт.
при условии отсутствия отдельной reservation policy, которая требует иного расчёта available stock.
96. ACCEPTANCE TEST — ORDER
Пользователь создаёт заказ.
Expected:
Order создаётся в Commerce;
получает MARU Order ID;
отправляется в ERP;
ERP возвращает External ID;
ID сохраняется;
повторная отправка не создаёт duplicate.
97. ACCEPTANCE TEST — PAYMENT
Payment provider отправляет:
SUCCESS
Expected:
Payment = PAID
Order = PAID
Повторная отправка того же webhook:
No duplicate
98. ACCEPTANCE TEST — PAYMENT FAILURE
Provider:
FAILED
Expected:
payment = FAILED;
order не получает PAID;
customer может повторить payment;
reservation обрабатывается согласно TTL.
99. ACCEPTANCE TEST — REFUND
Создать refund.
Expected:
refund отправляется provider;
provider подтверждает;
Commerce обновляет payment;
order получает корректный refund status;
ERP получает возврат;
audit record создан.
100. ACCEPTANCE TEST — SHIPPING
[8/15/2026 1:57 PM] Ada: Создать shipment.
Expected:
provider получает order;
возвращает shipment ID;
tracking number сохраняется;
customer видит tracking;
status обновляется webhook/polling.
101. ACCEPTANCE TEST — MARKETPLACE
Изменить stock MARU:
100 → 80
Expected:
Marketplace connector получает:
80
Повторная синхронизация не должна создавать duplicate listing.
102. ACCEPTANCE TEST — CRM
Создать Request Quote.
Expected:
RFQ создаётся в Commerce;
передаётся CRM;
CRM ID сохраняется;
sales manager получает lead;
изменение статуса синхронизируется согласно CRM mapping.
103. ACCEPTANCE TEST — NOTIFICATION
После успешной оплаты:
OrderPaid
должен вызвать:
Email;
SMS при включённом канале;
CRM event;
analytics event.
Если SMS недоступен:
Order не должен отменяться.
104. ACCEPTANCE TEST — ANALYTICS
После покупки должен сформироваться:
purchase
с:
order ID;
currency;
value;
items.
При этом payment information и другие чувствительные данные не должны отправляться в analytics.
105. ACCEPTANCE TEST — RETRY
Отключить ERP.
Создать заказ.
Expected:
заказ остаётся в Commerce;
integration event попадает в queue;
выполняются retries;
после восстановления ERP событие доставляется;
duplicate order не создаётся.
106. ACCEPTANCE TEST — DEAD LETTER QUEUE
Искусственно создать permanent integration error.
Expected:
retry выполняется;
после лимита сообщение переносится в DLQ;
создаётся alert;
администратор видит ошибку;
доступен manual retry.
107. ACCEPTANCE TEST — DATA CONFLICT
Изменить цену в Master System и вторичной системе.
Expected:
Master System имеет приоритет;
secondary system получает корректное значение;
conflict фиксируется в log.
108. ACCEPTANCE TEST — SECURITY
Попытаться:
отправить invalid webhook;
изменить payment status;
получить чужой order;
использовать чужой CRM ID;
вызвать admin integration endpoint без authorization.
Все попытки должны быть отклонены.
109. ACCEPTANCE TEST — MONITORING
При искусственной ошибке ERP:
Dashboard должен показать:
failed requests;
integration name;
error;
timestamp;
retry count.
Alert должен быть отправлен согласно configured severity.
110. INTEGRATION DEVELOPMENT SEQUENCE
Рекомендуемый порядок реализации:
Phase 1
Commerce Core integration framework.
Phase 2
ERP / 1С.
Phase 3
Payment.
Phase 4
Shipping.
Phase 5
CRM.
Phase 6
Notifications.
Phase 7
Marketplace.
Phase 8
Analytics.
Phase 9
WhatsApp / Telegram.
111. ПРИОРИТЕТЫ
Интеграция
Приоритет
ERP / 1С
P0
Payment
P0
Shipping
P0
CRM
P1
Email/SMS
P1
Analytics
P1
Marketplace
P1
WhatsApp
P2
Telegram
P2
112. ФИНАЛЬНАЯ АРХИТЕКТУРА
                         MARU E-COMMERCE
                                │
                         COMMERCE CORE
                                │
                       INTEGRATION LAYER
                                │
       ┌───────────────┬────────┼─────────┬───────────────┐
       │               │        │         │               │
       ▼               ▼        ▼         ▼               ▼
      ERP             CRM    Payment   Shipping       Marketplace
       │               │        │         │               │
       ▼               ▼        ▼         ▼               ▼
    1C/ERP            CRM     Local/    Local/          Uzum/
                              Global     Global          Others
       
       ┌───────────────────────────────────────────────────┐
       │                                                   │
       ▼                                                   ▼
 Notifications                                         Analytics
 SMS / Email / WA                                      GA4 / Meta
113. КЛЮЧЕВОЙ ПРИНЦИП ДЛЯ РАЗРАБОТЧИКА
Разработчик не должен проектировать бизнес-логику интеграции самостоятельно.
Для каждой интеграции должны быть заранее определены:
Master System.
Direction.
Data Mapping.
API Contract.
Authentication.
Webhook.
[8/15/2026 1:57 PM] Ada: Retry.
Timeout.
Idempotency.
Error Handling.
Logging.
Monitoring.
Acceptance Tests.
114. ИТОГ
ТЗ №4 создаёт Integration Layer MARU, который отделяет Commerce Core от внешних систем.
Главная архитектурная цепочка:
MARU Commerce Core → Integration Layer → ERP / CRM / Payment / Shipping / Marketplace / Notifications / Analytics
При этом:
1С не управляет frontend;
payment provider не управляет Order Engine;
marketplace не становится Master для каталога;
CRM не становится Master для заказов;
внешняя ошибка не должна разрушать checkout;
повторный webhook не должен создавать duplicate;
временная недоступность внешней системы обрабатывается через queue/retry;
все критические операции должны быть idempotent;
каждая интеграция должна иметь monitoring и audit trail.
ТЗ №4 является основанием для следующего документа — ТЗ №5: DevOps, QA, Security, Testing, Deployment и эксплуатация MARU E-commerce.