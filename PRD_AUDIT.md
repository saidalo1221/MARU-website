# PRD coverage audit (2026-09-30)

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
- **Idempotency**: no `Idempotency-Key` on checkout. A retried checkout is
  stopped in practice because the cart is deactivated, but the client gets
  "cart is empty" instead of the existing order. Webhooks are idempotent via
  unique provider transaction ids (Payme/Click); confirm-payment is
  idempotent because same-status transitions are no-ops. Not checked: refund
  double-submit.
- **RFQ number**: quotes have a numeric id only, not `RFQ-2026-000123`.
- **Attribution**: no UTM / landing page / referrer capture (TZ4 §18).
- **Server-side ad tracking**: events are stored, not forwarded to GA4/Meta
  (needs your credentials).
- **Structured logging / request ids**: request ids exist only in
  `IntegrationLog`; there is no request-id middleware.
- **Stock mismatch / reconciliation jobs** (TZ4 §26, §68-69): none.
- Not checked in depth: tax region/order-value inputs, promo edge cases,
  B2B minimum order enforcement.

## Missing
- **Shipments and tracking**: no shipments table, carrier adapter, tracking
  number or "Track Order" (TZ2 §25, TZ3 §32, TZ4 §29-33). Delivery is a rate
  calculation only.
- **ERP / 1C** integration and ID mapping table (TZ4 §6-13).
- **Marketplace connectors** incl. Uzum as a marketplace (Uzum exists only as
  a payment method name).
- **GDPR / privacy**: no cookie consent, data export or deletion (TZ3 §102).
- **Security headers** (HSTS, X-Frame-Options, CSP, nosniff) are not set in
  the app; needs to be done at the reverse proxy or added as middleware.
  Swagger UI (`/docs`, `/openapi.json`) is on in every environment.
- **Wishlist "notify me when available"**, **save for later** in the cart,
  **free-shipping threshold**, **delivery estimate on the product page**,
  **newsletter signup** (TZ2 §20, §29, §43; TZ3 event list).
- **Webhook pipeline** as described in TZ4 §50 (queue between receipt and
  handler) and a **real queue/worker** (retries are cron sweeps).
- **Integration health status + dashboard** beyond the log list.
- **Dockerfile, CI/CD, staging, monitoring, alerting, backups** (TZ3
  §82-96): none in the repo.
- **Sentry / error tracking**, **CDN + image optimisation**.

## n/a (stack difference)
Next.js SSR, NestJS modules, PostgreSQL JSONB/UUID keys, OpenSearch,
Redis-queue, Kubernetes. The app uses integer keys, per-locale translation
tables, MariaDB, and Redis only for rate limits.

## Suggested order
1. Shipments + tracking (customer-visible gap, TZ2 P0 "Order").
2. Security headers at the proxy; decide on `/docs` exposure.
3. Idempotency key on checkout; RFQ numbering.
4. Dockerfile + CI + backup/restore runbook (none exist).
5. ERP/1C and marketplace only after the vendor/API decisions.
