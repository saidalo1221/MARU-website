# MARU — start here (updated 2026-09-30, after the shipments pass)

Read this file, then `CLAUDE.md` (house rules). Open `HANDOFF.md` only for
detail on a specific area — it is long. `PRD.md` is the spec. Ignore
`session_notes.md` and the "done" lists in `TODO.md` (historical).
Also: `PRD_AUDIT.md` (what the PRD asks for vs what exists, with a suggested
build order) `MARIADB_PREFLIGHT.md` (first-deploy checklist for MariaDB
and the Python 3.9 server) and `OPS_RUNBOOK.md` (cron jobs, backups, restore,
container, proxy checklist). This file holds the to-do list; those three are
reference.

## What this is
Plastic-food-container e-commerce site. FastAPI + SQLAlchemy backend, React +
Tailwind frontend (Vite), MariaDB in production (UzCloud), SQLite `dev.db`
locally. All work is on branch `feat/client-analytics-events`, pushed to
origin, **PR #1 open** against `main` (`gh` is not installed; use the GitHub
web UI). The branch also carries 11 earlier commits that were never on
`origin/main`, so the PR is large. Working tree is clean.

## Run it
Backend MUST override DATABASE_URL or every DB call 500s:
```
cd "C:\Users\user\Desktop\best one yet"
DATABASE_URL=sqlite:///dev.db python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
cd frontend && npm run dev -- --host 127.0.0.1      # http://127.0.0.1:5173
```
- No `--reload` (it silently fails to restart here). Restart the backend by
  hand after backend edits: find PID with `netstat -ano | grep :8000`, then
  `taskkill //F //T //PID <pid>`.
- The frontend calls the backend directly at :8000. Requesting `/api/...` on
  :5173 returns HTML with a 200 — that proves nothing.
- Dev servers may already be running. Check ports 8000/5173 first.
- Accounts: `testuser1@example.com` / `TestPass123!` (super_admin). Admin login
  needs an emailed 2FA code (SMTP is configured). Do not run `dev_seed.py`
  against the existing `dev.db`.

## State: what exists
Storefront (catalog, product page, cart, checkout, accounts, blog, B2B forms,
SEO, ru/uz/en, multi-currency), full admin panel, auth hardening (admin 2FA,
customer new-device 2FA, lockout), payment adapters (Payme/Click/Stripe/PayPal,
unconfigured), Bitrix24 CRM push. Recently added and browser-verified on
2026-09-30: product badges, variant image gallery with hover-zoom, lightbox,
mp4 + YouTube entries, Quick View, cart upsell (`GET /cart/recommendations`),
country banner, dark mode, mobile filter bottom sheet, skeleton loaders,
WCAG fixes (lang sync, skip link, field labels, contrast), rate limits on
nearly every public route, FAQ in ru/uz. Client-side analytics
(`POST /analytics/events`, `frontend/src/lib/analytics.js`): `view_item`,
`select_variant`, `view_item_list`, `search`, `view_cart`, `begin_checkout`
(on checkout open), `add_payment_info` — browser-verified 2026-09-30; the
server no longer records `begin_checkout` at order placement. Also done and
verified (tests; shipments also in the browser): **shipments + order tracking**
(`shipments`/`shipment_events`, admin panel on the order page, status sync to
the order, emails, customer order page, public `/track` by order number +
email; manual carrier, no carrier API), **checkout `Idempotency-Key`**,
security headers + `/docs` off unless `ENABLE_DOCS=true` (add that to your
local `.env` if you want Swagger), upload magic-byte checks, `utcnow()`
removed, `remove_from_cart`/`refund` events (already existed; now tested).
Written but **never run**: `Dockerfile`, `.github/workflows/ci.yml`,
`scripts/backup_db.sh`.

## What is left (priority order)
Buildable now:
1. ~~Client-side analytics events~~ — DONE, including `remove_from_cart` and
   `refund` (server-side, tested).
2. ~~Accessibility follow-ups~~ — DONE (PR #1): `useDialogFocus` trap on
   every modal, `role="alert"`/`status`, axe pass (public + admin, light +
   dark, 390px checkout). Re-run axe after UI changes.
3. Not browser-verified: real mp4/webm upload in the admin variant-images
   panel (add-by-YouTube-URL was verified), real phone, Safari/Firefox.
4. ~~Shipments, security headers, idempotency, RFQ numbering (already
   existed), Dockerfile/CI/backups, `utcnow()`, upload byte checks~~ — done
   (see State). Remaining from `PRD_AUDIT.md` that needs no decision:
   proxy-side security headers (server config), request-id/structured
   logging, UTM/referrer attribution, free-shipping threshold, delivery
   estimate on the product page, newsletter signup, "notify me when
   available", save-for-later, GDPR export/deletion, stock reconciliation job.
5. Native-speaker review of the ru/uz FAQ text (my draft). `dev.db` has it but
   is gitignored — a real DB needs it entered via admin "Support Pages Content".

Needs a decision/access from the user (do not guess):
6. GA4 / Meta forwarding (needs Measurement Protocol secret + Meta token).
7. Object storage (S3-compatible): uploads are local-disk only.
8. Keep or drop Stripe/PayPal. Vendors: shipping carrier, SMS/WhatsApp/
   Telegram, ERP/1C, Uzum marketplace, Uzum Pay (needs API docs).
9. Admin MFA policy (code forces 2FA on all admin roles; TODO.md says opt-in).
10. `CountryBanner` sends every visitor's IP to `ipapi.co` from the browser,
   no consent step — privacy decision before launch.

Deployment blockers:
11. Production server has only Python 3.9. `X | None` annotations were
    rewritten to `Optional[...]` (static checks pass) but it has **not** been
    run on a real 3.9 — see `MARIADB_PREFLIGHT.md` for the server-side check.
12. MariaDB never run. SQL files match the models (static diff), one
    InnoDB-only deadlock risk was fixed; the first-deploy checklist is in
    `MARIADB_PREFLIGHT.md`. PRD coverage is in `PRD_AUDIT.md`.
13. Rate limits key on `request.client.host`: behind a reverse proxy run
    uvicorn with `--proxy-headers --forwarded-allow-ips=<proxy>` or all users
    share one bucket. Route `/sitemap.xml` to the backend too.
14. Prod `.env`: `REDIS_URL` (+ Redis running), `BITRIX24_WEBHOOK_URL`,
    `FRONTEND_URL`, Payme/Click credentials. Schedule
    `app/tasks/sync_exchange_rates.py` daily. Swap Gmail SMTP for a
    transactional provider (env-only change).
15. Nothing is deployed. Code is pushed (PR #1) but not merged to `main`.
16. Confirm the real DB user: `.env` uses `maru`, `CLAUDE.md` says `maruplast`.
    Requirements are unpinned; after one green run on the server, freeze them.

## Gotchas that cost time
- **Windows Python defaults to cp1251.** Always `open(..., encoding="utf-8")`
  or work in bytes when scripting edits; a bare `open()` corrupted an em dash
  once. Console prints Cyrillic as `?` — write to a UTF-8 file and Read it.
- Source files are CRLF in the working tree; preserve endings in scripted
  edits or diffs balloon. `git` LF/CRLF warnings are noise.
- Translations live in `frontend/src/i18n/translations.js`; every new UI string
  needs en + ru + uz. A single unescaped apostrophe in an Uzbek string breaks
  the whole file — verify by importing it with node after editing.
- Money in admin goes through `<Money>` / `AdminCurrencyContext`. New public
  pages need `<Seo>`. Per-locale translation pattern is described in
  HANDOFF.md ("Conventions").
- Payme/Click webhooks are deliberately NOT rate-limited (shared provider IPs,
  signature-authenticated).
- Chrome tool: `resize_window` does not change the viewport. Test phone widths
  with a same-origin `<iframe style="width:390px">` from a scratch page.
- Background dev servers can be killed by Claude Code under memory pressure;
  don't restart them automatically if told not to.
- Tests: `conftest.login` completes the emailed-code step itself (admin
  2FA, customer new-device) by capturing the code from the notifier; use it
  instead of posting to `/auth/login` directly.
- Analytics trackers must guard with a `useRef` (pages refetch when the cart
  currency loads, and StrictMode double-runs effects) or events get counted
  2-3x per visit.
- `dev.db` may hold throwaway analytics events from browser testing
  (anonymous rows); clear before real use.
- axe-core in the browser: inject it from cdnjs into the page and run it per
  page (a SPA pushState loop can stall in a hidden tab — use one full load
  per page, e.g. in a same-origin iframe). Transitions make color-contrast
  read mid-fade values; inject `*{transition:none!important}` first.
- Browser-testing checkout in dev: no payment provider is configured, so
  there are no payment radios, and seeded products have one variant. Stub the
  API response with a `window.fetch` patch in the page rather than editing
  `dev.db`.
- `python -m app.init_db` on SQLite creates `BIGINT` primary keys that SQLite
  will not auto-increment (inserts fail with `NOT NULL constraint failed:
  <table>.id`). Only `dev_seed.py` and `tests/conftest.py` patch that. New
  tables in `dev.db` need the `@compiles(BigInteger, "sqlite")` patch (see
  `dev_seed.py`) when created. `shipments`/`shipment_events` and
  `orders.idempotency_key` were already added to `dev.db` this way.
- Admin browser-testing without the emailed code: run the backend on a
  *copy* of `dev.db`, set `admin_mfa_verified_until` on the admin row in the
  copy, mint a token with `create_access_token(str(user.id))` and put it in
  `localStorage.maru_access_token`.
- Testing pattern that works: FastAPI `TestClient` against a *copy* of
  `dev.db` (`DATABASE_URL=sqlite:///<copy>`), never the real one.

## Working rules (from CLAUDE.md)
Verify before editing, smallest correct change, no new dependencies unless
necessary, stop and explain if something looks destructive to the database.
Commit only when asked; end commits with the Co-Authored-By line the session
specifies.
