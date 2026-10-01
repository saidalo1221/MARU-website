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
