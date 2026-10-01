# MARU - start here (updated 2026-10-01, end of the build session)

Read this file first, then `CLAUDE.md` (house rules). Everything here was checked against the code, the test suite and the
browser; nothing is copied from older notes. If you are a new session: the build is feature-complete except for items that need
accounts or documents from the owner (section 4). Do not rebuild anything listed as done.

## 1. Which doc to trust
| File | Use |
|---|---|
| `START_HERE.md` (this) | Current state, owner decisions, what is left, how to work in this repo. |
| `PRD.md` | The four specs (ТЗ №1-4). The block at the top is the build status: `[x]` built and tested, `[!]` blocked with the reason. |
| `NOTES.md` | Every assumption made while building, numbered, newest last. Read items 37+ for the last sessions. |
| `INTEGRATIONS.md` | Adapters, inbound/outbound webhooks, documents, web push, remarketing and consent, markets, loyalty. |
| `OPS_RUNBOOK.md` | Cron jobs / worker, backups and restore, recovery targets, release flow. |
| `MARIADB_PREFLIGHT.md` | First-deploy checklist. `WHATSAPP_TEMPLATES.md`: message templates to submit to Meta. |
| `PRD_AUDIT.md`, `HANDOFF.md`, `Done.md`, `session_notes.md`, `TODO.md` | History only; parts are out of date. |

## 2. Owner decisions (what the owner said, and where it now lives)
**Decided and built**
- **Carrier:** MARU delivers itself (the admin picks it); an external carrier API is not planned. Tracking numbers are generated.
- **Recovery targets (approved):** data loss up to 24 h at launch, 1 h once MariaDB binary-log shipping is on; restore within 4 h. See `OPS_RUNBOOK.md`.
- **Tax classes:** the owner chose to keep every product on the standard class for now. Changing a product's class is an admin action on the
  product page; tax rules by class are in Admin > Tax rules.
- **Hold lifted:** the payments ledger (`payments` table, `orders.payment_status`) was built when the owner said go.
- **Credentials supplied by the owner** (they live only in the git-ignored `.env`, never in git; all were pasted in chat, so rotate them
  before launch): Telegram bot, GA4 measurement id + secret, Meta pixel id + Conversions API token. Meta and GA4 were verified
  against the platforms (Meta test event received). Staff alerts reach the owner's Telegram chat.
- **Decisions handed to the admin panel** (the owner wants the business to decide these, not the code):
  | Decision | Where the admin makes it | Default until they choose |
  |---|---|---|
  | Which products are sold in which countries | Admin > Markets (bulk) or the product page | Every product sold everywhere |
  | Loyalty: points per USD, point value, max share of an order payable with points | Admin > Loyalty | 1 point per USD, 1 point = 0.01 USD, max 50% |
  | Loyalty: which customer types take part | Admin > Loyalty | Retail only |
  | Loyalty: tiers (threshold + earning multiplier) and point expiry (days) | Admin > Loyalty | No tiers, points never expire |
  | What each SKU costs (profit and margin) | Admin > SKU costs (inline edit or paste a list) | Empty: dashboard shows "n/a" |
  | Monthly ad spend (CAC and ROAS) | Admin > Dashboard (marketing section) | Empty: CAC/ROAS show "n/a" |
  | Loyalty point adjustments, promo codes (products, categories, countries, customers, limits), shipping rates, exchange rates | their Admin pages | n/a |
- **Cookie banner has three choices:** analytics (own statistics + campaign attribution), advertising (GA4/Meta server events), geolocation.
  GA4/Meta get events only with the advertising choice (`X-Ads-Consent` header; orders remember it in `orders.ads_consent`). Visitors who accepted
  before the split are asked again. The privacy-policy text is editable in Admin > Support-page content; the owner/lawyer should mention advertising there.

**Still open (owner must decide / supply)** - see section 4.

## 3. State of the code
- Branch `feat/client-analytics-events`. Commit and push only when the owner asks (they have asked each time so far).
- Tests: `python -m pytest -q` (about 400 tests, ~2.5 min; run single files while iterating). Frontend: `cd frontend && npm run build`, and
  `for f in tests/*.mjs; do node $f; done` (includes an i18n key check). Lint: `python -m ruff check app tests scripts --select E9,F63,F7,F82`.
- Backend FastAPI + SQLAlchemy 2; dev DB is SQLite (`dev.db`, gitignored); target is MariaDB 10.5 on Python 3.9. Frontend React + Vite + Tailwind,
  i18n ru/uz/en in `frontend/src/i18n/translations.js` (every string needs all three).
- **Nothing has ever run on MariaDB.** `app/schema_mariadb.sql` (fresh install) and `app/migration_2026_session10/11/12.sql` (upgrade) are hand-written; tests check
  the schema file matches the models and that migration literals match enum NAMES (SQLAlchemy stores enum names in upper case, e.g. `'PAID'`).
  Run the migrations on a copy first.
- Catalogue, filters, search and suggestions run in SQL and page on the server (about 0.2 s per page at 20 000 products on SQLite).
- Background work: DB job queue (`python -m app.tasks.worker`, needed when `JOBS_ASYNC=true`); cron tasks listed in `deploy/crontab.example`.

## 4. What is left
**Blocked on the owner** (accounts, documents or keys):
- **WhatsApp:** built (templates in `WHATSAPP_TEMPLATES.md`); needs `WHATSAPP_PHONE_NUMBER_ID`, a permanent token, approved templates, a test phone.
- **SMS:** needs a provider (Eskiz.uz / PlayMobile ...), credentials, an approved sender name.
- **Customer Telegram:** needs the deployed site (webhook) and customers pressing Start in the bot.
- **ERP/1C and Uzum/marketplace:** need API docs + credentials (adapter interfaces, id mapping and events are ready).
- **Payments:** Payme, Click, Stripe, PayPal are built from public docs but untested; need sandbox keys. Saved cards need a provider vault (not built).
- **Google Ads conversion tag:** needs conversion id + label. **Figma:** needs a designer (the next planned step is implementing a design the owner brings from Claude Design).

**Never run anywhere:** MariaDB migrations; the worker/systemd unit; the nginx rules in `deploy/nginx.conf.example` (bot prerender, `/sw.js` no-cache);
CI on GitHub; Python 3.9; web push in a real browser; any real payment.

**Before going live:** run migrations on a MariaDB copy; production `.env` (no `META_TEST_EVENT_CODE`; its own VAPID keys from `scripts/generate_vapid.py`, kept forever;
`JOBS_ASYNC`, `REDIS_URL`, SMTP, `DOCUMENTS_DIR` on a persistent volume); rotate the Telegram/GA4/Meta credentials; enable binary-log shipping; set up staging;
the business enters SKU costs, ad spend, markets, loyalty settings.

## 5. Working in this repo (lessons that cost time)
- Many files use CRLF: edit with a script that preserves line endings. Python files are written with the Write tool; very long bash commands that
  contain apostrophes can fail to parse, so write scripts to the scratchpad and run them.
- `i18n_add.py`-style helpers silently skip keys that already exist: after adding translations, run `node frontend/tests/i18n-keys.mjs` and check
  the visible text (a dashboard label once showed the wrong sentence).
- SQLite tests cannot see MariaDB problems: keep SQL files in sync with models (a test guards it) and write enum literals as NAMES.
- Always run the frontend build after editing JSX (a missing `{}` once slipped through until the build).
- Never put credentials in git, NOTES, or chat summaries; `.env` is git-ignored. Do not push unless asked.

## 6. If the owner brings a design
Implement tokens first (`frontend/src/styles/tokens.css`, `tailwind.config.js`), then shared components (`components/ui/*`, header/footer), then pages by
priority, checking each at 375 px and desktop, in dark mode, and in all three languages; keep tests, build and the accessibility checks green.
