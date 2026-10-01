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
