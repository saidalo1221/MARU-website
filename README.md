# MARU

Online shop for MARU plastic food containers: a React storefront and admin panel on a FastAPI backend.
Retail and wholesale, three languages (ru, uz, en), light and dark theme.

| Part | Stack |
|---|---|
| Storefront and admin | React 18, Vite, Tailwind CSS 3, framer-motion, react-router |
| Backend | Python 3, FastAPI, SQLAlchemy |
| Database | MariaDB 10.5 in production (`maruplast`); SQLite for local work |
| Cache and rate limits | Redis (optional locally) |

Other documents: `START_HERE.md` (current state and owner decisions), `LAUNCH_CHECKLIST.md` (what is left before
going live), `OPS_RUNBOOK.md` (running the site), `DESIGN_SYSTEM.md` (colours, type, shapes), `INTEGRATIONS.md`
(Telegram, WhatsApp, Bitrix24, analytics), `NOTES.md` (assumptions made while building), `PRD.md` (the requirements).

## Run it on your computer

You need Python 3.11+ and Node 20+.

**1. Backend**

```bash
python -m venv .venv
.venv\Scripts\activate                 # Windows. On macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root (it is git-ignored). The smallest working file:

```
SECRET_KEY=any-long-random-string-of-32-or-more-characters
DATABASE_URL=sqlite:///./dev.db
CORS_ORIGINS=http://localhost:5173
```

Create the tables and demo data, then start the API (the demo seed is for a fresh, throwaway SQLite file):

```bash
set DATABASE_URL=sqlite:///./dev.db     # macOS/Linux: export DATABASE_URL=sqlite:///./dev.db
python -m app.dev_seed
python -m uvicorn app.main:app --reload --port 8000
```

The API is then at `http://127.0.0.1:8000/api/v1`. Interactive API docs are off unless `ENABLE_DOCS=true`.

**2. Frontend**

```bash
cd frontend
npm install
npm run dev                             # http://localhost:5173
```

`frontend/.env.local` points the storefront at the API (`VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`, the
default). Copy `frontend/.env.example` if it is missing.

**3. An admin account**: `python scripts/create_admin.py you@example.com` (asks for a password; add `--role` for a
narrower role such as `marketing_manager`). Admin sign-in sends a code by e-mail, so SMTP has to be configured (below).

## Settings (`.env`)

Every setting is read in `app/config.py`. Real environment variables win over `.env`.

| Group | Variables |
|---|---|
| Core | `SECRET_KEY`, `DATABASE_URL`, `ENVIRONMENT` (`production` on the server), `ENABLE_DOCS`, `LOG_LEVEL` |
| Addresses | `FRONTEND_URL` (links in e-mails and Telegram), `BACKEND_URL` (uploaded image addresses), `CORS_ORIGINS` (comma separated), `CORS_ORIGIN_REGEX` (local development only) |
| E-mail | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_USE_TLS` |
| Payments | `PAYME_MERCHANT_ID`, `PAYME_KEY`, `CLICK_SERVICE_ID`, `CLICK_MERCHANT_ID`, `CLICK_SECRET_KEY`, `STRIPE_SECRET_KEY`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_API_BASE` |
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID`, `TELEGRAM_ALERT_LANG` |
| Analytics | `GA4_MEASUREMENT_ID`, `GA4_API_SECRET`, `META_PIXEL_ID`, `META_CAPI_TOKEN` |
| Infrastructure | `REDIS_URL`, `JOBS_ASYNC` (needs the worker running), `CACHE_ENABLED` |

Frontend build settings go in `frontend/.env.local`: `VITE_API_BASE_URL` (required for a production build),
`VITE_STRIPE_PUBLISHABLE_KEY`, `VITE_PAYPAL_CLIENT_ID`.

## Tests and checks

```bash
python -m pytest -q                     # backend, uses an in-memory database and never touches your real one
cd frontend
node tests/i18n-keys.mjs                # every text key exists in ru, uz and en
npm run build                           # production build into frontend/dist
python scripts/launch_preflight.py      # from the root: is this configuration ready for real customers?
```

## What is in the shop

**Storefront**: landing page, catalogue with filters, product pages with several photos per variant, cart and
checkout, order status and tracking, wishlist, account (orders, addresses, profile, privacy), blog, wholesale / B2B and
distributor pages, support pages (delivery, payment, returns, FAQ, contact).

**Admin** (`/admin`): orders, customers, products and photos, stock and warehouses, prices and markets, promo codes,
reviews, loyalty, blog, notifications, newsletter, integrations log, webhooks, audit log, staff accounts.

### Editing the landing page and SEO (Admin > Marketing)

- **Landing page text** (`/admin/landing-page`): change any text on the home page for each language. An empty field keeps
  the built-in text. FAQ questions are edited in *Page sections*, reviews in *Reviews*, products in *Products*.
  Edits are stored in the `content_overrides` table and replace the matching text key everywhere it is shown.
- **SEO** (`/admin/seo`): per page and per language, set the title, description, share image and "hide from Google".
  The title is used exactly as typed. Stored in the `seo_meta` table; product pages take their tags from the product.
- Both appear on the site after a page refresh. The two tables are in `app/migration_2026_session12.sql` for MariaDB.

### Telegram alert for new orders

When an order is placed, the bot sends a message to `TELEGRAM_ADMIN_CHAT_ID` with the customer, phone, items,
totals, payment, delivery address, a Google Maps link and a link to the order in the admin. It is sent in the
background, so Telegram being slow or down never delays checkout.

- `TELEGRAM_ALERT_LANG` picks the language of the message: `ru` (default), `uz`, `en`, or `order` to use the language
  the customer ordered in.
- Setup: create a bot with @BotFather, put its token in `TELEGRAM_BOT_TOKEN`, send the bot a message from the chat or
  group that should receive alerts and put that chat's id in `TELEGRAM_ADMIN_CHAT_ID`.
- The test suite blanks the token, so tests never message the real chat.

### Motion and effects (storefront)

Built with framer-motion; nothing extra to install. All of it is switched off for visitors with "reduce motion" set.

| Effect | File |
|---|---|
| Page change (fade and rise, none inside account and admin) | `frontend/src/components/motion/PageTransition.jsx` |
| Scroll progress line | `ScrollProgress.jsx` |
| Headline words sliding up | `WordReveal.jsx` |
| Text band that speeds up with scrolling | `VelocityMarquee.jsx` |
| Cards tilting toward the cursor | `TiltCard.jsx` |
| Buttons pulled toward the cursor | `Magnetic.jsx` |
| Cursor light inside tiles | `Spotlight.jsx` |
| Numbers counting up | `CountUp.jsx` |

They are used in `frontend/src/pages/Home.jsx` and `frontend/src/components/home/MarqueeHero.jsx`.

## Project layout

```
app/                  FastAPI backend: routers/, models/, schemas/, services/, tasks/ (jobs, cron)
app/migration_*.sql   MariaDB changes, applied in order (see MARIADB_PREFLIGHT.md)
frontend/src/         pages/, components/ (admin pages in pages/admin), context/, api/, i18n/translations.js
scripts/              create_admin.py, launch_preflight.py, remove_demo_data.py, backup_db.sh, generate_vapid.py
deploy/               nginx, systemd and cron examples
tests/                backend tests (pytest)
```

New visible text goes into `frontend/src/i18n/translations.js` in all three languages (`en`, `ru`, `uz`).

## Before real customers

Follow `LAUNCH_CHECKLIST.md`: a working MariaDB user, public https addresses, a payment provider, a real mail
service, and removing the demo data (`python scripts/remove_demo_data.py`, add `--apply` to delete). Photos and
products in the demo catalogue are placeholders (`IMAGE_CREDITS.md`).
