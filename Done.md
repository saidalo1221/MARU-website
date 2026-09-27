MARU Session Handoff Summary

  Repo: C:\Users\user\Desktop\best one yet — git-initialized, 7 commits, working tree clean. TODO.md is the living source of truth; this summary is
  a snapshot of it.

  What's built and tested this session (65 tests, pytest tests/ -v, all passing)

  1. Stock reservation moved to order-creation time with a TTL (fixes a real race condition), atomic per-warehouse locking
  2. PAYMENT_FAILED/PARTIALLY_REFUNDED order states, fully wired into Payme/Click webhook retry flows
  3. Refunds — partial + full, Stripe/PayPal real (unverified live), Payme/Click correctly blocked (no verified API)
  4. Multi-warehouse inventory (single-warehouse-per-line reservation, documented as not split-fulfillment)
  5. Quote → Order conversion
  6. Email verification + TOTP admin MFA (opt-in, not forced)
  7. Redis-backed rate limiting (graceful in-process fallback)
  8. CRM integration retry/dead-letter-queue system
  9. Tax engine, notification templates (DB-overridable)
  10. /api/v1 URL prefix (breaking change, frontend updated to match)
  11. Server-side analytics event capture (not forwarded to GA4/Meta — no credentials)
  12. Live FX rate sync via exchangerate-api.com (real key in .env, never committed) — manual/cron-only, never per-request
  13. app/dev_seed.py — committed, reusable local dev seeder (catalog, warehouse, shipping, exchange rates, RU/UZ translations)
  14. Ran frontend against backend end-to-end for the first time; found and fixed two real bugs: order_type: "legal_entity" mismatch (backend only                                  No changes this session
      accepts "individual"/"company"), and checkout's delivery fee stuck on "TBD"

  Genuinely blocked — needs the user, not more building

  - Production server has only Python 3.9.9; this code needs 3.10+ (X | None syntax). Confirmed via shell on the actual UzCloud box. Real
    deployment blocker.
  - MariaDB access: real DB is 10.5.29-MariaDB, user maru/saidalo2011, reachable only from inside the UzCloud server (localhost:3306) — not from
    here. User was mid-way through enabling remote access when we moved on.
  - Migrations not yet run against real MariaDB (app/migration_new_tables.sql + app/migration_2026_session2.sql, or fresh app/schema_mariadb.sql) —
    full SQL ready, just unexecuted there.
  - Vendor decisions still open: Stripe/PayPal keep-or-drop, Uzum Pay (no docs), shipping carrier, SMS provider, ERP/1С, object storage (blocks
    invoices), GA4/Meta credentials.
  - app/tasks/expire_reservations.py, retry_integrations.py, sync_exchange_rates.py all need actual cron/Task Scheduler entries — they only run
    opportunistically or on-demand right now.

  Frontend gaps (unchanged, not touched beyond the two bug fixes)

  Missing pages: B2B, Wholesale, Distributor, About, Contact, Delivery, Payment, Returns, FAQ, Blog. No UI yet for
  quote/wishlist/addresses/reviews/forgot-password. No country selector/geo-detect banner.

  Currently running locally (if still up)

  Backend on 127.0.0.1:8000 (SQLite dev.db), frontend on localhost:5173, both seeded via app/dev_seed.py with fake Payme test credentials.