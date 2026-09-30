# PRD coverage audit (2026-09-30, updated after the shipments/hardening pass)

**Updated since first written:** shipments + tracking, checkout idempotency,
security headers, `/docs` switch, upload signature checks and the ops files
(Dockerfile, CI, backup runbook) now exist - see the struck-through items
below. RFQ numbering was already implemented; the earlier audit was wrong.

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
- **Payment status as its own field/table**: PRD TZ3 §29-31 wants
  `orders.payment_status` and a unified `payments` table with
  `idempotency_key`. Here payment state lives in `orders.status` plus
  Payme/Click transaction tables; Stripe/PayPal only store
  `payment_reference`. Works, but there is no single payment ledger.
- **Idempotency**: ~~no `Idempotency-Key` on checkout~~ **done**: optional
  `Idempotency-Key` header; a retry returns the original order (owner-only,
  `orders.idempotency_key` unique). Without the header a retry still gets
  "cart is empty". Webhooks are idempotent via
  unique provider transaction ids (Payme/Click); confirm-payment is
  idempotent because same-status transitions are no-ops. Not checked: refund
  double-submit.
- ~~**RFQ number**~~: already implemented (`RFQ-<year>-<id>`, `routers/quotes.py`).
- ~~**Attribution**~~ **done**: UTM/referrer/landing path stored on the order.
- **Server-side ad tracking**: events are stored, not forwarded to GA4/Meta
  (needs your credentials).
- ~~**Structured logging / request ids**~~ **done** (middleware, tagged lines, optional
  JSON format, optional Sentry hook that needs `sentry-sdk` installed).
- ~~**Stock reconciliation**~~ **done** as a report (`reconcile_stock`, `--fix` opt-in).
  No automatic alerting on top of it.
- Not checked in depth: tax region/order-value inputs, promo edge cases,
  B2B minimum order enforcement.

## Missing
- ~~**Shipments and tracking**~~ **done (manual carrier)**: `shipments` +
  `shipment_events`, admin create/update, status sync to the order, email on
  status change, customer order page + public `/track` (order number +
  email). Still missing: a carrier API adapter (needs a carrier decision)
  and automatic tracking updates.
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
- **Integration health status + dashboard** beyond the log list.
- **Dockerfile, CI/CD, backups**: now in the repo (`Dockerfile`,
  `.github/workflows/ci.yml`, `scripts/backup_db.sh`, `OPS_RUNBOOK.md`) but
  **none has been run** (no Docker, no GitHub run, no server access).
  Still none: staging, monitoring, alerting (TZ3 §82-96).
- **Sentry / error tracking**, **CDN + image optimisation**.

## n/a (stack difference)
Next.js SSR, NestJS modules, PostgreSQL JSONB/UUID keys, OpenSearch,
Redis-queue, Kubernetes. The app uses integer keys, per-locale translation
tables, MariaDB, and Redis only for rate limits.

## Suggested order
1. ~~Shipments + tracking~~ done (manual carrier).
2. ~~Security headers; `/docs`~~ done in the API; proxy side pending.
3. ~~Idempotency key; RFQ numbering~~ done / already existed.
4. ~~Dockerfile + CI + backup runbook~~ written, unverified.
5. ERP/1C and marketplace only after the vendor/API decisions.
