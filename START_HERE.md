# MARU — start here (rechecked 2026-10-01)

Everything below was re-verified from git, the filesystem, the test suite and
a build on 2026-10-01 — not copied from older notes. Read this file, then
`CLAUDE.md` (house rules). Do not read the rest unless you need it.

## Which doc to trust
- **This file**: current state + the to-do list.
- `PRD.md`: the spec. `PRD_AUDIT.md`: PRD vs. what exists (accurate, current).
- `MARIADB_PREFLIGHT.md`: first-deploy checklist (MariaDB + Python 3.9 server).
- `OPS_RUNBOOK.md`: cron jobs, backups/restore, container, proxy, CI.
- `HANDOFF.md`: history + "Conventions" section only. Its "PRD gap audit" and
  "Known gaps" sections are OUT OF DATE (e.g. they still say Quick View, the
  country banner and the cart upsell are unbuilt). Do not plan from them.
- `Done.md` (2026-09-27 snapshot), `session_notes.md`, `TODO.md`: historical.

## Verified state (2026-10-01)
- Branch `feat/client-analytics-events` @ `412edfc`, in sync with its origin
  at the last `git status`. Earlier notes say PR #1 is open — **not
  verifiable** (`gh` isn't installed; use the web UI).
- **The working tree is NOT clean and nothing from the 2026-10-01 session is
  committed**: 33 modified files plus two new ones
  (`app/migration_2026_session10.sql`, `tests/test_pricing_edge_cases.py`).
  See "Changed 2026-10-01" below. Review and commit when ready.
- `python -m pytest -q`: **190 passed in ~5-7 min** (slow; run single files while
  iterating). `npx vite build` in `frontend/`: passes.
- `dev.db` (gitignored, hand-patched) has all model tables and every column,
  including the session-10 tax columns (`tax_rules` was rebuilt; `orders.region`
  added). A backup from before that is NOT in the repo.
- Python 3.9: no `X | None` left; all 194 `.py` files parse with 3.9 grammar.
  **Never run on a real 3.9** (none installed here; CI and Dockerfile target 3.9).
- Dev servers are NOT running (ports 8000/5173 empty at last check).
- Never run, only written: `Dockerfile`, `.github/workflows/ci.yml`,
  `scripts/backup_db.sh`, everything in `deploy/` (nginx, systemd, crontab).

## Changed 2026-10-01 (uncommitted, tested, browser-checked unless noted)
- **MARU is its own carrier.** `ShipmentCreate.carrier` defaults to `MARU`; the
  admin form is pre-filled with it. A blank tracking number on a MARU shipment
  becomes `<order_number>-<n>`. Other carrier names still work (no auto number).
- **Refunds** lock the order row first (`db.refresh(order, with_for_update=True)`),
  so a concurrent double-submit can't pass the "exceeds total" check twice.
  Only proven on SQLite (it ignores row locks) — prove it on MariaDB.
- **Reconciliation alert:** `reconcile_stock` emails `ALERT_EMAIL` (new setting,
  not yet in any `.env`) when it finds drift.
- **Integration health:** `GET /admin/integration-logs/health` + cards on the
  admin Integration Logs page (HEALTHY / DEGRADED / FAILED / DISABLED over 24h).
- **B2B minimum order quantity** is now enforced at checkout
  (`MIN_ORDER_QUANTITY`). It was only a UI hint. Not enforced in the cart on
  purpose, so the quantity stepper doesn't error.
- **Promos:** the promo's `currency` is now honoured (minimum order amount and
  FIXED discount are converted to the cart currency); redemption is an atomic
  conditional UPDATE (`redeem_promo`), so the last use can't be taken twice.
- **Tax rules** gained an optional `region` (`*` = any) and `min_order_amount`
  (USD tiers). Lookup order: country, region, customer type; highest reached
  tier wins. Checkout has an optional "Region / state" field and `orders.region`
  stores it. Region field only shows for a *new* address — saved addresses have
  no region. **Needs `app/migration_2026_session10.sql` on MariaDB (never run).**
- **Order statuses are translated** on `/track`, the order page and order
  history (`orderStatus.statusLabels`, en/ru/uz; ru/uz are my draft).
- **Audit log coverage** (PRD §81) now includes: inventory create, SKU create,
  exchange rate create/update/delete/sync, promo create/update, shipping rate
  create/update, tax rule create/update, warehouse create/update, product
  update/delete, admin role promote/demote (helpers `audit_create` /
  `audit_update` in `app/services/audit.py`). **Still NOT audited:** content
  routes (blog, about, page sections, site settings, translations, uploads,
  categories, notification templates, reviews, variant images, product/variant
  create, integration retry) and auth/MFA events.
- **Cart minimum UX:** cart lines carry `min_order_quantity`; the cart page shows
  "Minimum order: N" (red while below) and disables checkout until every line
  meets it.
- **Statuses translated everywhere** (storefront + admin orders list/detail/
  history/filters). Quote, review and integration-log statuses in admin are
  still raw. The customer order page now labels the payment *method* correctly.
- axe (WCAG 2.0/2.1 A+AA) re-run in the browser on /cart, /checkout (new-address
  form), /track, admin tax rules (form open), integration logs, orders list and
  order detail: **0 violations**.
- UI fixes: footer newsletter input was squeezed to ~40px; checkout region
  input is debounced (per-keystroke requests came back out of order and left
  the totals on a stale region's tax).

## Run it
Backend MUST override DATABASE_URL or every DB call 500s:
```
cd "C:\Users\user\Desktop\best one yet"
DATABASE_URL=sqlite:///dev.db python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
cd frontend && npm run dev -- --host 127.0.0.1      # http://127.0.0.1:5173
```
- No `--reload` (it silently fails to restart here). After backend edits: find
  the PID with `netstat -ano | grep :8000`, then `taskkill //F //T //PID <pid>`.
- The frontend calls the backend directly at :8000. `/api/...` on :5173 returns
  HTML with a 200 — that proves nothing.
- `/docs` is off unless `ENABLE_DOCS=true` in `.env`.
- Accounts: `testuser1@example.com` / `TestPass123!` (super_admin). Admin login
  needs an emailed 2FA code (SMTP is configured). Never run `dev_seed.py`
  against the existing `dev.db`.

## What exists
FastAPI + SQLAlchemy backend (49 models, ~40 routers, cron tasks in
`app/tasks/`: expire_reservations, notify_back_in_stock, reconcile_stock,
retry_integrations, sync_exchange_rates). React + Tailwind frontend, ru/uz/en,
multi-currency, dark mode, full admin panel. Highlights:
- Storefront: catalog, product page (badges, multi-image gallery with zoom,
  lightbox, mp4 + YouTube), Quick View, cart (upsell via
  `GET /cart/recommendations`, save for later, free-shipping progress),
  checkout (`Idempotency-Key`), accounts, blog, B2B/quote forms, SEO + sitemap,
  newsletter double opt-in, back-in-stock alerts, public order tracking at
  `/track`, `/privacy` + `/terms`, GDPR export and self-service erasure
  (`/account/privacy`).
- Security: admin 2FA, customer new-device 2FA, lockout, rate limits on nearly
  every public route (webhooks deliberately exempt), API security headers,
  upload magic-byte checks, request-id logging (`LOG_FORMAT=json`, optional
  `SENTRY_DSN`, needs `pip install sentry-sdk`).
- Consent: `ConsentBanner` + `lib/consent.js` gate the `ipapi.co` lookup, client
  analytics and stored UTM attribution; default is nothing until the visitor
  chooses; footer "Cookie settings" withdraws.
- Analytics: client events via `POST /analytics/events` + `lib/analytics.js`;
  server events for purchase/refund/etc. Stored only — not forwarded anywhere.
- Ops: shipments (MARU is the carrier; admin-entered events, no carrier API),
  stock reconciliation report + email alert, integration health view,
  UTM attribution on orders, payment adapters (Payme/Click/Stripe/PayPal —
  real code, no live credentials), Bitrix24 CRM push.
- Schema: all migrations through `app/migration_2026_session9.sql`, plus
  `app/schema_mariadb.sql` for fresh installs. **SQLite-tested only.**

## To do — buildable now
1. **Browser checks still open:** real mp4/webm *playback* (the 2026-10-01
   upload test used an empty webm container, so only the upload/attach path was
   proven), a real phone, Safari/Firefox, and re-running axe after the
   2026-10-01 UI changes beyond the pages listed above. Already browser-verified on 2026-10-01: newsletter
   double opt-in, privacy/erasure, `/track`, back-in-stock, save-for-later,
   admin tax form + checkout region, MARU shipment form, health cards.
2. **Native-speaker review** of ru/uz text: FAQ (my draft; `dev.db` has it but is
   gitignored — a real DB needs it via admin "Support Pages Content") and the
   legal pages.
3. `frontend/public/robots.txt` has a relative `Sitemap:` line (crawlers ignore
   it) — make it absolute once the domain is known.
4. Per `PRD_AUDIT.md`, still open: no unified payments ledger /
   `payment_status` (**on hold at the user's request**); product-level tax and a
   region on saved addresses; health metrics (latency/queue/lag) and alerts
   beyond the reconciliation email; per-product/customer promo targeting; no
   webhook queue / real worker (retries are cron sweeps); audit coverage for the
   content/auth routes listed above.

## To do — needs a decision or access from the user (don't guess)
- **Legal**: `/privacy` and `/terms` are drafts written from what the code does
  (`frontend/src/i18n/legal.js`); a lawyer must review them and the operator's
  legal name, registration and governing law must be added (Site Settings only
  holds phone/email/address). Account erasure **keeps orders and B2B quotes**
  (incl. name/address snapshots) — confirm that is acceptable or scrub them.
  Server-side events (`add_to_cart`, `purchase`, …) and OpenStreetMap tiles in
  the address picker are NOT consent-gated — ask the lawyer.
- Carrier is decided (MARU itself). Still open: whether warehouse managers can
  create shipments, and whether MARU delivery needs fees/zones beyond the
  existing shipping rates.
- GA4 / Meta forwarding (needs Measurement Protocol secret + Meta token).
- Object storage (S3-compatible): uploads are local-disk only.
- Keep or drop Stripe/PayPal. Vendors: SMS/WhatsApp/Telegram, ERP/1C, Uzum
  marketplace, Uzum Pay (needs API docs).
- Admin MFA policy (code forces 2FA on all admin roles; `TODO.md` says opt-in).
- Real DB user: `.env` uses `maru`, `CLAUDE.md` says `maruplast`. Requirements
  are unpinned — freeze them after one green run on the server.

## To do — deployment blockers
1. Run on a real Python 3.9 (see `MARIADB_PREFLIGHT.md`).
2. Run the MariaDB SQL files on a real server (never done), **including
   `migration_2026_session10.sql`** (drops and re-adds the tax_rules unique
   key), + full smoke test. Prove the refund row lock and the atomic promo
   redeem there too.
3. Behind a reverse proxy run uvicorn with
   `--proxy-headers --forwarded-allow-ips=<proxy>` or every visitor shares one
   rate-limit bucket. Route `/sitemap.xml` to the backend. The proxy must add
   the static-frontend security headers (`deploy/nginx-security-headers.conf`).
4. Prod `.env`: `REDIS_URL` (+ Redis running), `BITRIX24_WEBHOOK_URL`,
   `FRONTEND_URL`, `BACKEND_URL`, Payme/Click credentials, `ALERT_EMAIL`. Install the cron
   jobs (`deploy/crontab.example`). Swap Gmail SMTP for a transactional
   provider (env-only change).
5. Commit the 2026-10-01 work, push, merge the PR, deploy. Nothing is deployed.

## Gotchas that cost time
- **Windows Python defaults to cp1251.** Always `open(..., encoding="utf-8")`
  or work in bytes when scripting edits. Console prints Cyrillic as `?` — write
  to a UTF-8 file and Read it.
- Working-tree files are CRLF; preserve endings in scripted edits. Git's
  LF/CRLF warnings are noise.
- A very long `python - <<'EOF'` heredoc in the Bash tool can fail with a
  quoting error; use the Write tool for big files.
- Translations: `frontend/src/i18n/translations.js`; every new UI string needs
  en + ru + uz. One unescaped apostrophe in an Uzbek string breaks the whole
  file — import it with node after editing to check.
- Money in admin goes through `<Money>` / `AdminCurrencyContext`. New public
  pages need `<Seo>`. Per-locale translation pattern: see HANDOFF.md
  "Conventions".
- Payme/Click webhooks are deliberately NOT rate-limited (shared provider IPs,
  signature-authenticated).
- Tests: `conftest.login` completes the emailed-code step itself (admin 2FA,
  customer new-device) by capturing the code from the notifier — use it instead
  of posting to `/auth/login`. Test against a *copy* of `dev.db`
  (`DATABASE_URL=sqlite:///<copy>`), never the real one.
- Analytics trackers must guard with a `useRef` (pages refetch when the cart
  currency loads and StrictMode double-runs effects) or events count 2-3x.
- `dev.db` may hold throwaway analytics events from browser testing; clear
  before real use.
- `python -m app.init_db` on SQLite makes `BIGINT` primary keys that SQLite
  won't auto-increment (`NOT NULL constraint failed: <table>.id`). Only
  `dev_seed.py` and `tests/conftest.py` patch that; new tables in `dev.db` need
  the `@compiles(BigInteger, "sqlite")` patch (see `dev_seed.py`).
- Chrome tool: `resize_window` does not change the viewport — test phone widths
  with a same-origin `<iframe style="width:390px">` from a scratch page.
- axe-core in the browser: inject it from cdnjs and run it per page (a SPA
  pushState loop can stall in a hidden tab — use one full load per page, e.g. in
  an iframe). Inject `*{transition:none!important}` first or contrast reads
  mid-fade values.
- **Running the real SMTP in dev sends real mail.** `.env` points at Gmail, which
  hit its daily limit during testing (550). The app still answers 202 and logs
  the failure. Blank `SMTP_HOST` for local runs, or stub the notifier.
- The Chrome tool's Enter key did not submit forms and typing into a ref
  sometimes missed; click the button and click-then-type by coordinates. A hidden
  tab also stops `MediaRecorder`/canvas capture (empty webm).
- Browser-testing checkout in dev: no payment provider is configured (no
  payment radios) and seeded products have one variant. Stub the API response
  with a `window.fetch` patch rather than editing `dev.db`.
- Admin browser-testing without the emailed code: run the backend on a *copy* of
  `dev.db`, set `admin_mfa_verified_until` on the admin row in the copy, mint a
  token with `create_access_token(str(user.id))` and put it in
  `localStorage.maru_access_token`.
- Background dev servers can be killed by Claude Code under memory pressure;
  don't restart them automatically if told not to.

## Working rules (from CLAUDE.md)
Verify before editing, smallest correct change, no new dependencies unless
necessary, stop and explain if something looks destructive to the database.
Commit only when asked; end commits with the Co-Authored-By line the session
specifies.
