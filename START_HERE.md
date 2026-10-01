# MARU - start here (rewritten 2026-10-01 after a full re-audit)

Read this file, then `CLAUDE.md` (house rules). Everything here was checked against the code, the test suite and the
browser on 2026-10-01, not copied from older notes.

## Which doc to trust
- **This file**: how to run things, current state, what is left.
- `PRD.md`: the four specs; the block at the top is the build status (`[x]` built and tested, `[!]` blocked with the reason).
- `NOTES.md`: every assumption made while building (numbered), in order.
- `INTEGRATIONS.md`: adapters, webhooks (in and out), documents, field mapping.
- `OPS_RUNBOOK.md`: cron jobs / worker, backups and restore, recovery targets, release flow.
- `MARIADB_PREFLIGHT.md`: first-deploy checklist. `WHATSAPP_TEMPLATES.md`: the message templates to submit to Meta.
- `PRD_AUDIT.md`, `HANDOFF.md`, `Done.md`, `session_notes.md`, `TODO.md`: history; may be out of date.

## Run it
- Backend: `python -m uvicorn app.main:app --port 8000` (settings from `.env`; dev DB is SQLite `dev.db`, gitignored).
  After pulling model changes run the dev DB sync (adds missing tables/columns to a SQLite file).
- Frontend: `cd frontend && npm install && npm run dev` (needs the backend on :8000).
- Tests: `python -m pytest -q` (about 370 tests, ~2 minutes) and `cd frontend && for f in tests/*.mjs; do node $f; done`.
- Worker (queued e-mail, webhooks, GA4/Meta/WhatsApp sends): `python -m app.tasks.worker` (or `--once` from cron). Only
  needed when `JOBS_ASYNC=true`; otherwise those run inside the request.
- Load check: `python scripts/load_test.py http://127.0.0.1:8000 --users 20 --seconds 30` against a staging copy.

## State
- Branch `feat/client-analytics-events`; all work is committed. CI (`.github/workflows/ci.yml`): lint, tests, build,
  i18n key check, dependency scan - never run on GitHub yet.
- Database: **nothing has ever run on MariaDB.** `app/schema_mariadb.sql` (fresh install) and
  `app/migration_2026_session10/11/12.sql` (upgrade) were written by hand; tests check that the schema file matches the
  models and that migration literals match the enum names (SQLAlchemy stores enum NAMES in upper case).
- Catalogue, filters, search and suggestions run in SQL and page on the server (about 0.2 s per page at 20 000 products on
  SQLite); the storefront never downloads the whole catalogue.

## Built (see `PRD.md` for the full checklist)
Storefront (catalogue, search, product, cart, guest checkout, account, B2B/quote, content pages, blog), admin panel
(orders, customers, products, stock transfers, promos, tax, shipping, documents, reviews, webhooks, jobs, dashboard,
audit log), payments ledger, order documents (confirmation / invoice / proforma / packing list), outbound and inbound
webhooks, job queue, GA4 + Meta server-side events, Telegram staff alerts, WhatsApp template sends (unverified),
abandoned-cart e-mail, prerendered pages for crawlers.

## Blocked on you (see the `[!]` lines in `PRD.md`)
ERP/1C, Uzum, SMS provider, WhatsApp credentials + approved templates, Payme/Click/Stripe/PayPal sandbox keys,
customer Telegram (needs the deployed site), Figma.

## Before going live
Run the migrations on a copy of MariaDB first; set the production `.env` (no `META_TEST_EVENT_CODE`, real
`JOBS_ASYNC`, `REDIS_URL`, SMTP, `DOCUMENTS_DIR` on a persistent volume); rotate every credential that was pasted into
chat (Telegram bot, GA4 secret, Meta token); enable binary-log shipping for the 1-hour data-loss target; add the
`/prerender` proxy rule from `deploy/nginx.conf.example`; set up staging.
