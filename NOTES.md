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
