# PRD coverage audit (2026-09-30; updated 2026-10-01 after the audit-fix pass)

**Updated since first written:** shipments + tracking, checkout idempotency,
security headers, `/docs` switch, upload signature checks and the ops files
(Dockerfile, CI, backup runbook) now exist - see the struck-through items
below. RFQ numbering was already implemented; the earlier audit was wrong.

**Updated 2026-10-01 (uncommitted work, 186 tests passing):** refund
double-submit, reconciliation alerting, the integration health view, B2B
minimum order quantity, promo currency + atomic redemption, tax region and
order-value tiers, and MARU as its own carrier are now done - struck through or
noted below. The payments ledger is deliberately **on hold**.

What the code actually implements against PRD TZ №2-№4, from reading the
backend (`app/`) and grepping the frontend. "Verified" means I read the code
path; "not checked" means I did not dig in. This corrects an earlier rough
list that overstated what is missing.

The PRD recommends Next.js + NestJS + PostgreSQL. The product is React/Vite +
FastAPI + MariaDB (fixed by `CLAUDE.md`). Stack items below are therefore
marked **n/a**, not missing.

## Implemented (verified in code)
- **Order state machine** with an explicit allowed-transition table, status
  history rows and audit log entries (`order_service.py`). Includes
  PAYMENT_FAILED, PARTIALLY_REFUNDED, RETURNED, REFUNDED.
- **Inventory**: reserve at order creation under `SELECT ... FOR UPDATE`,
  release on cancel/return/refund/failure, reservation TTL with an expiry
  sweep (`app/tasks/expire_reservations.py`), one-warehouse-per-line choice by
  warehouse priority (PRD TZ3 §68 manual priority).
- **Price snapshots**: order and order-item price, name, SKU and company
  fields are copied at checkout; a later price change does not touch history.
- **Pricing pipeline**: customer-type price, quantity tiers, promo codes,
  tax (`tax_rules`, country + customer type), shipping rates, in PRD order.
- **Multi-currency** (`exchange_rates`, live sync) and **ru/uz/en**.
- **Cancel / refund**: customer cancel endpoint, admin refunds with a
  `refunds` table and provider refund call where the gateway supports it.
- **Payments**: Payme, Click (JSON-RPC webhooks, unique transaction ids),
  Stripe, PayPal (polling confirm). Gateway adapter interface + registry.
- **CRM adapter** (Bitrix24) with `IntegrationLog`, retry sweep, dead-letter
  status and an admin manual-retry endpoint (TZ4 §52-57).
- **Notification adapter** boundary + templates (email implemented; SMS /
  WhatsApp / Telegram are placeholders, no provider chosen).
- **Security**: backend RBAC via `require_role` on every admin router, admin
  2FA, customer new-device 2FA, account lockout, rate limits, audit log.
- **Reviews** only from customers with a paid order containing the product.
- **API versioning** under `/api/v1`; FastAPI generates OpenAPI.
- **B2B**: quote/wholesale/distributor requests into a `quote_requests`
  table, pushed to CRM, admin quote management.
- **Analytics**: client events + server events (`analytics_events`).

## Partial / differs from PRD
- **Payment status as its own field/table** (on hold at the user's request;
  not started): PRD TZ3 §29-31 wants
  `orders.payment_status` and a unified `payments` table with
  `idempotency_key`. Here payment state lives in `orders.status` plus
  Payme/Click transaction tables; Stripe/PayPal only store
  `payment_reference`. Works, but there is no single payment ledger.
- **Idempotency**: ~~no `Idempotency-Key` on checkout~~ **done**: optional
  `Idempotency-Key` header; a retry returns the original order (owner-only,
  `orders.idempotency_key` unique). Without the header a retry still gets
  "cart is empty". Webhooks are idempotent via
  unique provider transaction ids (Payme/Click); confirm-payment is
  idempotent because same-status transitions are no-ops. ~~Refund
  double-submit~~ **done**: `create_refund` locks the order row first, so a
  concurrent duplicate re-reads the first refund's status and total (proven on
  SQLite only; SQLite ignores row locks - prove it on MariaDB).
- ~~**RFQ number**~~: already implemented (`RFQ-<year>-<id>`, `routers/quotes.py`).
- ~~**Attribution**~~ **done**: UTM/referrer/landing path stored on the order.
- **Server-side ad tracking**: events are stored, not forwarded to GA4/Meta
  (needs your credentials).
- ~~**Structured logging / request ids**~~ **done** (middleware, tagged lines, optional
  JSON format, optional Sentry hook that needs `sentry-sdk` installed).
- ~~**Stock reconciliation**~~ **done** as a report (`reconcile_stock`, `--fix`
  opt-in) ~~with no alerting~~ **now emails `ALERT_EMAIL`** when it finds drift.
- ~~**Tax region / order-value inputs**~~ **done**: `tax_rules.region` and
  `min_order_amount` (USD tiers), checkout "Region / state" field, `orders.region`.
  Still missing: product-level tax (PRD TZ3 §74 lists product as an input) and a
  region on saved addresses. Needs `migration_2026_session10.sql` on MariaDB.
- ~~**Promo edge cases**~~ **fixed**: the promo's `currency` was ignored (a 5 USD
  discount took 5 UZS off a UZS cart); the used-count increment was a plain
  read-modify-write that two concurrent checkouts could both win. Now converted
  and an atomic conditional UPDATE. Per-product/per-customer targeting is still
  deferred (documented on the model).
- ~~**B2B minimum order enforcement**~~ **fixed**: `min_order_quantity` was only a
  UI hint; checkout now rejects lines below it (`MIN_ORDER_QUANTITY`). Not
  enforced in the cart on purpose.

## Missing
- ~~**Shipments and tracking**~~ **done (manual carrier)**: `shipments` +
  `shipment_events`, admin create/update, status sync to the order, email on
  status change, customer order page + public `/track` (order number +
  email). **Carrier decision made (2026-10-01): MARU delivers itself**, so the
  carrier defaults to `MARU` and a blank tracking number is generated
  (`<order_number>-<n>`); an external carrier API adapter is no longer planned.
  Tracking updates are admin-entered.
- **ERP / 1C** integration and ID mapping table (TZ4 §6-13).
- **Marketplace connectors** incl. Uzum as a marketplace (Uzum exists only as
  a payment method name).
- **GDPR / privacy**: data export and self-service erasure **done** (orders/quotes
  retained). Cookie-consent banner **done** (gates analytics, attribution and the
  `ipapi.co` lookup). Privacy Policy and Terms pages **drafted** (need legal review).
- ~~**Security headers**~~ **done for the API** (middleware in `main.py`);
  the reverse proxy must add them for the static frontend (see
  `OPS_RUNBOOK.md`). ~~Swagger UI on everywhere~~ now off unless
  `ENABLE_DOCS=true`.
- ~~Wishlist "notify me when available", save for later, free-shipping threshold,
  delivery estimate, newsletter signup~~ all **done** (TZ2 §20, §29, §43).
- **Webhook pipeline** as described in TZ4 §50 (queue between receipt and
  handler) and a **real queue/worker** (retries are cron sweeps).
- ~~**Integration health status + dashboard**~~ **done (basic)**:
  `GET /admin/integration-logs/health` and cards on the Integration Logs page
  (HEALTHY/DEGRADED/FAILED/DISABLED from the last 24h; DISABLED = CRM webhook not
  configured). Still missing: latency, queue size and sync-lag metrics (TZ4 §66),
  and alerts beyond the reconciliation email.
- **Dockerfile, CI/CD, backups**: now in the repo (`Dockerfile`,
  `.github/workflows/ci.yml`, `scripts/backup_db.sh`, `OPS_RUNBOOK.md`) but
  **none has been run** (no Docker, no GitHub run, no server access).
  Still none: staging, monitoring, alerting (TZ3 §82-96).
- **Sentry / error tracking**, **CDN + image optimisation**.

## n/a (stack difference)
Next.js SSR, NestJS modules, PostgreSQL JSONB/UUID keys, OpenSearch,
Redis-queue, Kubernetes. The app uses integer keys, per-locale translation
tables, MariaDB, and Redis only for rate limits.

## Verified in a browser on 2026-10-01
Newsletter double opt-in, self-service erasure, `/track`, back-in-stock
signup + notify task (stubbed mailer), save-for-later, admin tax form + checkout
region repricing, MARU shipment form, integration health cards, admin video
upload + attach (empty webm only - playback not proven). Not yet: a real phone,
Safari/Firefox, axe after the latest UI changes.

## Suggested order
1. ~~Shipments + tracking~~ done (manual carrier).
2. ~~Security headers; `/docs`~~ done in the API; proxy side pending.
3. ~~Idempotency key; RFQ numbering~~ done / already existed.
4. ~~Dockerfile + CI + backup runbook~~ written, unverified.
5. ERP/1C and marketplace only after the vendor/API decisions.
6. Payments ledger (on hold), product-level tax, then a real queue/worker.
