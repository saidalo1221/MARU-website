# NOTES — assumptions made while building from PRD.md

Per the CLAUDE.md instruction not to ask questions, ambiguous points are decided here.
Newest entries last. Blocked items are marked `[!]` in the BUILD STATUS block at the top of PRD.md.

1. **Stack.** PRD TZ3 recommends Next.js/NestJS/PostgreSQL. CLAUDE.md fixes React/Tailwind, FastAPI and MariaDB, so
   stack-specific wording (UUID keys, JSONB, SSR, NestJS modules) is treated as satisfied by the existing equivalents.
2. **Catalog filtering stays client-side in the UI.** The API now supports server-side filters, sort and paging
   (`/products/?category_id&capacity&color&material&availability&price_min&price_max&sort&page&limit`, `X-Total-Count`),
   but the storefront catalog is small and already loads the full list, so the page filters it in the browser and pages it
   at 12 per page.
3. **Material filter** is only shown when more than one material exists (the DB currently only allows polypropylene).
4. **Card "Add to Cart"** is shown only for products with exactly one SKU that is in stock; multi-variant products use
   the quick view / product page to choose.
5. **Wishlist heart on cards** sends signed-out visitors to the login page.
6. **Tests no longer send real email.** `tests/conftest.py` now blanks `SMTP_HOST` for every test (the developer `.env`
   holds real SMTP credentials and registration tests were trying to send mail).
7. **Navigation menus are click/keyboard driven** (no hover), so they work on touch screens; they close on Escape,
   outside click and item choice.
8. **Country selector** in the header stores the delivery country in `localStorage` (`maru_ship_country`); it drives the
   product-page delivery block and is the default country at checkout. Browsing is never blocked by it (TZ2 §42).
9. **"Sets / Packs"** have no data model (no pack SKUs), so the menu entry and home block ("Pack of 3/5/7") explain that
   packs are bought by choosing a size and a quantity, with quantity discounts where configured. No savings are claimed.
10. **Home page claims** use only facts present in the data (polypropylene, own production per the PRD, five sizes,
    availability shown per product). No certificates or quality claims are made (TZ2 §44). Manufacturing and Quality pages
    show only what an admin enters (Admin > Support Pages Content, new keys `manufacturing` / `quality`).
11. **Reviews block** on the home page appears only when approved reviews with text exist; it shows first names only.
12. **Social links** are optional site settings; the footer shows only the ones that are set. Payment chips show only
    payment methods that are configured and enabled.
13. **Password policy**: customers need 8+ characters with a letter and a digit (and not a common password); admin roles
    need 12+ with upper/lower case, a digit and a symbol, enforced when they change or reset a password. Existing passwords
    are not re-checked. Tokens are stateless, so changing a password does not sign out other sessions.
14. **Phone numbers** are stored as digits with an optional leading `+` (E.164 shape, TZ4 §80); input formatting is stripped.
15. **Retrying a payment** is only offered for redirect-style gateways (Payme, Click), whose webhooks already handle a
    re-reserve after failure; card gateways need a new checkout.
16. **Migrations** for this run accumulate in `app/migration_2026_session12.sql` (never run on MariaDB).
17. **Quantity tiers** had no admin or public surface although pricing used them. Added: `PUT /admin/skus/{id}/tiers`
    (replaces the set; minimum quantity 2+, audited), tiers in the public SKU output (converted with the display currency),
    an admin editor, and a tier table on the product page. A tier never raises the price above the SKU's own price.
18. **"Delivery from X"** ignores pickup-style methods (any method whose name contains "pick"), so a free pickup does not
    make delivery look free.
19. **Search stays client-side** (catalog is small): typo tolerance is edit distance 1 for words of 4-6 letters and 2 for
    7+, none for 1-3 letters. `frontend/tests/search.test.mjs` checks the logic (`node tests/search.test.mjs`, no new dependency).
20. **Product-page "benefits"** are the product description and specification table; no separate benefits field was added.
21. **Sale price**: a `special_price` below the retail price is treated as the SKU's sale price - it drives the Sale
    badge, the struck-through old price and the discount in the storefront, and (new) is charged to retail customers.
    Other customer types keep their own price column; `special` customers pay it as before.
22. **Guest checkout** is open (no login redirect). After a guest order the order page offers "Create an account"
    (email prefilled). Orders stay reachable through the per-order token kept in the browser session.
23. **Login by phone** uses the same login form field: an `@` means email, otherwise a phone normalised to digits with an
    optional `+`. A number shared by several accounts never matches. The new-device emailed-code step still applies.
24. **Local payment gateways (Payme, Click) are Uzbekistan-only** (assumption: they settle in UZ); other destinations do
    not see them, and checkout rejects them with a 400. Stripe and PayPal are offered everywhere.
25. **FAQ topics** are an optional category on FAQ page sections (products, orders, payment, delivery, returns, wholesale,
    international); sections without one appear first as "General". The old hard-coded FAQ strings in the translation file
    are unused and were left in place.
26. **Country choice can switch the currency** (e.g. Germany -> EUR) but only to a currency the store has a rate for;
    the visitor can change it back with the currency selector.
27. **Wholesale page tables** list the real minimum order quantity, price and quantity tiers per product; nothing is invented.
28. **Category pages** live at `/shop/:slug` and reuse the catalog (pinned to the category and its subcategories). Content
    (description, SEO text, image URL, per-language overrides) is edited under Admin > Categories. The category FAQ block
    shows the first general FAQ questions (the FAQ topics are not tied to product categories). The sitemap lists category pages.
29. **Design tokens** are CSS variables in `frontend/src/styles/tokens.css`, read by `tailwind.config.js`; brand colours stay
    the temporary placeholders (PRD §45.2: do not invent brand colours). See `DESIGN_SYSTEM.md`.
30. **Error display**: `errorMessage()` hides every 5xx and any HTML/long server text behind the caller's friendly fallback;
    `ErrorBoundary` wraps the app. `html { overflow-x: hidden }` (pre-existing) can mask overflow, so layout was checked
    element by element at 375px instead.
31. **No Figma**: design-file artifacts (§59, §65) are marked blocked in PRD.md.
32. **Error body**: every API error keeps FastAPI's `detail` and now also has `error: {code, message, request_id}` (TZ3 §50).
    Business errors raised as "CODE: message" supply their own code; unhandled exceptions return a generic 500 with a request id
    and no stack trace (the traceback is in the log).
33. **Paging**: orders (admin and customer), quotes, reviews, integration logs and blog posts take `?page` and `?limit` (default 50,
    max 100) and return `X-Total-Count`. Audit log (<=500), analytics events (<=500), newsletter (<=1000) and the public blog
    (<=100) keep their existing caps because they are admin-internal.
34. **Dates**: the API returns UTC without a marker; `frontend/src/lib/format.js` parses them as UTC and shows them in the visitor's
    timezone and the site language (this fixes times being shown as if they were local).
35. **Audit rows** record the caller's IP (as seen by the app; behind a proxy it needs `--proxy-headers`) and the request id.
36. **Roles**: PRD lists B2B_CUSTOMER and ADMIN; the code has customer types (retail/wholesale/distributor/export/special) for B2B
    customers and SUPER_ADMIN plus the five manager roles. Treated as equivalent; no new roles were added.
37. **Job queue**: the database is the queue (table `jobs`, `SELECT ... FOR UPDATE SKIP LOCKED` on MariaDB) instead of adding
    Celery/RQ - no new dependency, and Redis stays optional. `JOBS_ASYNC=false` by default (emails sent inside the request, as
    before); production should set it to true and run the worker. Retries back off 1/5/15/30/60 min, 5 attempts, then the job is
    "dead" (dead-letter queue) and an admin retries it via `POST /admin/jobs/{id}/retry`. Not run against real MariaDB.
38. **Inbound webhooks**: `POST /api/v1/integrations/{provider}/webhook`, HMAC-SHA256 over `"<timestamp>.<body>"`, 5 min tolerance,
    secrets in `WEBHOOK_SECRETS` JSON. The signing scheme is my choice (no provider spec was given); events are stored and queued
    but no connector consumes them until a vendor (1C, Uzum, ...) is chosen.
39. **Cache**: public categories / site settings / exchange rates are cached 5 min (`CACHE_TTL_SECONDS`, `CACHE_ENABLED`); Redis if `REDIS_URL` is set, else process memory. Any committed ORM change to the underlying tables clears the cache automatically (SQLAlchemy session events), so no admin route has to remember to. Raw SQL writes do not clear it (TTL covers them). Several workers without Redis can show stale data for up to the TTL.
40. **Order documents**: stored on local private disk (`DOCUMENTS_DIR`, outside /static) rather than object storage (none provisioned); the 5-minute signed link is a JWT with a `doc` claim, not a user token. Admins can upload/void but not download (they have the original).
41. **Image variants**: new uploads are named `img-<hex>` and get 320/800/1600 WebP copies via Pillow (added to requirements.txt - the only way to resize images); older images and GIFs have none and render as before. AVIF skipped (needs an extra Pillow plugin). No CDN/object storage was provisioned; put nginx caching/CDN in front of /static.
42. **Phones**: checkout, saved addresses and quotes now normalise to digits + optional + and reject fewer than 7 or more than 15 digits.
43. **Payments ledger**: table `payments` (one row per attempt) plus `orders.payment_status`, driven from the single `set_order_status()` choke point so every path (webhooks, confirm-payment, admin, refunds, expiry) updates it. A paid order that is then cancelled stays `paid` until a refund moves it. AUTHORIZED exists in the enum but nothing sets it (no gateway authorizes without capturing). The backfill SQL in migration session12 uses MariaDB syntax and has NOT been run anywhere - run it on a copy first. Payme/Click keep their own endpoints; the PRD path `/integrations/payments/{provider}/webhook` was not added.
44. **Telegram**: the bot token lives only in the git-ignored `.env` (TELEGRAM_BOT_TOKEN / TELEGRAM_BOT_USERNAME); tests blank it. The connector sends to a chat id and is used for staff alerts via TELEGRAM_ADMIN_CHAT_ID. Customer messages need each customer to press Start in the bot and a public webhook to learn their chat id - not built until the site is deployed. The token was pasted in chat, so it should be rotated in @BotFather once the site is live.
45. **GA4**: events are forwarded server-side via the Measurement Protocol (`integrations/ga4.py`) with a hashed anonymous client_id, no PII, and never for admin events. Because the server does not know the browser GA client_id, a server `purchase` shows as a separate GA visitor from the browsing session; link them later by sending the browser client_id with the checkout. Credentials are in the git-ignored `.env`; the secret was pasted in chat, so rotate it in GA4 (Admin > Data streams > Measurement Protocol API secrets) once live. Verified against Google validation endpoint (accepted, no messages). Meta/Conversions API still needs a pixel id and token.
46. **Meta Conversions API**: built (`integrations/meta.py`; purchase, add_to_cart, begin_checkout, sign_up, generate_lead, add_to_wishlist, view_item, search) and covered by mocked tests. Pixel 28511215335172968 with the supplied token is ACCEPTED by Meta's events endpoint (an intentionally incomplete test event was answered with a parameter error, not a permission error, and recorded nothing). A real event has not been sent, so end-to-end delivery is unconfirmed until a Test events code is set in META_TEST_EVENT_CODE. Credentials are in the git-ignored `.env`. Use META_TEST_EVENT_CODE on dev machines so development traffic never counts as real conversions. Matching is weak (hashed visitor id only, no email/phone).
47. **WhatsApp**: built against the Cloud API (`integrations/whatsapp.py`) but NOT verified against Meta: no token / phone number id / approved templates yet. Defaults I chose: three utility templates (order created, status changed, shipment update) in ru/uz/en (texts in WHATSAPP_TEMPLATES.md); messages only for customers who ticked an opt-in box at checkout (`orders.whatsapp_opt_in`, shown only when WhatsApp is configured); language = site language at checkout (`orders.language`, also now stored for future use); numbers without a country code are skipped; a 4xx from Meta is not retried. Needs migration session12 (two new orders columns).
48. **Product-level tax**: `products.tax_class` = standard | reduced | zero | exempt (default standard, so nothing changes until set). zero/exempt are never taxed; reduced uses a tax rule with class "reduced" and falls back to the general ("*") rule; the order-value tier is chosen from the whole cart total, the class then picks the rate per line. Order tax is the sum of per-line taxes (each rounded to the cent), stored on `order_items.tax_amount`. I did not decide which products are reduced/exempt - that is a tax-advisor call, all products start at standard. Tax rules gained `tax_class` in their unique key (migration drops and re-adds the unique index).
49. **Promo targeting**: a code can list product ids and/or category ids (sub-categories included); the discount applies only to matching lines (OR between the two lists), split across lines proportionally with the rounding remainder on the last one (`order_items.discount_amount`). The minimum order amount counts matching lines only, and a targeted code is rejected when nothing in the cart matches. Per-country targeting is still not built. **Per-customer limit**: `max_uses_per_customer`, counted per account id or checkout email (case-insensitive) from `promo_redemptions`, ignoring cancelled / payment-failed orders so those give the use back. Guests are only checked at checkout (the cart preview does not know their email).
50. **AVIF**: new uploads also get -320/-800/-1600 `.avif` copies when Pillow can write AVIF (native since Pillow 11.3, so no extra package; requirements say pillow>=11.3). Storefront cards and the product gallery use <picture> with AVIF, WebP, original. Older uploads are unchanged. Pillow 12 needs Python 3.10+; on the Python 3.9 server pip will install Pillow 11.x.
51. **Recovery targets approved by the owner (2026-10-01)**: RPO 24 h at launch, 1 h once binlog shipping is on; RTO 4 h. Product tax classes: owner chose to keep every product on standard.
52. **Outbound webhooks** (TZ1 §37): admin-managed endpoints (super admin) get signed POSTs for order.created / paid / cancelled / shipped / delivered, payment.success / failed and inventory.updated, using the same HMAC scheme as inbound webhooks. Deliveries are jobs (retry, dead letters). https only and no internal addresses unless WEBHOOK_ALLOW_PRIVATE_URLS (dev); redirects are not followed. Order events include the customer name/email/phone - intended for systems the company owns. With JOBS_ASYNC off they run immediately; with it on a worker must be running.
53. **Dashboard** (TZ1 §27-28, 59-60): see app/services/dashboard.py docstring for each definition (paid orders only, USD, UTC days, visitors = analytics sessions, gross profit only over SKUs with a cost price). CAC/ROAS need manually entered ad spend. "Gross profit" and "CAC" show n/a until costs / spend are entered.
54. **Customers admin** (TZ1 §33): list/search/filter customers, change customer type (drives which price column applies), deactivate. Staff accounts stay on the Administrators page.
55. **Found in review**: the payments migration used lower-case enum values but SQLAlchemy stores enum NAMES (upper case) - fixed and guarded by tests/test_migration_enum_literals.py; i18n_add.py silently skips keys that already exist (caught a dashboard label collision) so use tests via frontend/tests/i18n-keys.mjs and check_specs.
56. **Catalogue at scale** (TZ1 §46): the product list endpoint, search (`?q=`), suggestions (`/products/suggest`) and filter choices (`/products/facets`) filter, rank, sort and page in SQL. Without ?limit the list is capped at 100. Typo tolerance uses a cached name index and edit distance (so a typo search costs about one pass over the cached names). Measured on SQLite with 20 000 products: ~0.2 s per page (was ~3 s per page at only 2 000). MariaDB not measured.
57. **Prerender** (TZ1 §29, TZ3 §85): crawlers/link-preview bots get server-rendered HTML from `/prerender/...` via the nginx user-agent map; default language is Russian (`?lang=` overrides). Not tested behind real nginx.
58. **Documents**: confirmation on order, proforma for company orders, invoice on paid, packing list on packed (all printable HTML served sandboxed; "Save as PDF" from the browser). Regenerating voids the earlier copy. No PDF engine was added (dependency).
59. **Abandoned cart / sets / related products / stock transfers / review photos / promo countries+customers**: built with the defaults described in the commit messages; sets are their own SKU with a contents list (own stock), not a computed bundle.
60. **Found in the full review**: payments migration enum literals (fixed, guarded by a test), order status history ties (fixed by id), admin page translations (privacy/terms), the dashboard "Orders" label colliding with an existing key, and the storefront downloading the whole catalogue (fixed). A schema-vs-models test now fails when the SQL file drifts.
61. **Loyalty**: retail accounts only (wholesale / distributor / export / special customers have their own price lists); 1 point per 1 USD of goods actually paid, 1 point = 0.01 USD, points may pay at most 50% of the goods (all editable in Admin > Loyalty); no expiry and no tiers were built (decision: keep it simple until the business wants them). Points are spread over the order lines like a promo discount so tax and documents stay consistent. A partial refund does not take earned points back (only a full refund / cancellation after payment does).
62. **Market assortment**: lists of country NAMES, compared case-insensitively with the delivery country the visitor chose; with no country chosen nothing is hidden. SQLite lower() only folds ASCII, so non-Latin country names match exactly on SQLite but fold properly on MariaDB. All products start unrestricted - which product goes to which market is a business decision I did not make.
63. **Web push** needs the new dependency `pywebpush` (it signs and encrypts the messages). A VAPID key pair was generated into the git-ignored .env; production needs its own (`scripts/generate_vapid.py`) and must keep it forever. Devices are linked to signed-in customers only (no guest push).
64. **Ad consent**: ad platforms now receive events only with the visitor's analytics consent (before, server events such as purchase were forwarded regardless). The banner's "analytics" choice is treated as covering ad measurement; if the legal text must separate them, add a third banner choice.
65. **Owner decisions delegated to the admin panel** (2026-10-01): market assortment (Admin > Markets, bulk), loyalty settings incl. eligible customer types, tiers and expiry (Admin > Loyalty), SKU costs (Admin > SKU costs, inline or paste import) and monthly ad spend (Dashboard). Defaults are the unrestricted / retail-only / no-tiers / no-expiry / empty-cost choices, so nothing changes until the business acts.
66. **Cookie banner third choice**: "advertising" is separate from "analytics". Ad platforms (GA4, Meta) now need the advertising choice (`X-Ads-Consent`, `orders.ads_consent`); first-party analytics events and campaign attribution still follow the analytics choice. Earlier consent records without the new field count as "not agreed".
67. **Loyalty extras**: eligible customer types are a setting (comma list); tiers use lifetime earned points and a multiplier; expiry removes unspent points oldest-first (daily task `expire_loyalty_points`, also applied when a customer opens their balance or spends points).
68. **Newsletter campaigns (Admin > Newsletter)**: a marketing manager writes a subject and plain-text message, sends a test to their own address, then queues it for every CONFIRMED subscriber (optionally one language). One `newsletter.send` job per recipient (retried, dead-lettered); a person who unsubscribes between queueing and sending is skipped. Each mail gets that person's own unsubscribe link appended. Without a worker (`JOBS_ASYNC=false`) lists of up to 25 are sent immediately; larger lists wait for `python -m app.tasks.worker`. Gmail SMTP caps about 500 mails a day: use a transactional mail service for real volume. Not built: HTML mails, scheduling, per-order "email the customer" action.
