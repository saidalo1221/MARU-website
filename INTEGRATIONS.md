# MARU integrations

How MARU talks to outside systems (PRD ТЗ№4 §70-83). Every integration goes through one of the adapter
interfaces in `app/services/integrations/adapters.py`; until a vendor is chosen the adapter is a "Null" one
that does nothing and logs it.

## Building blocks

| Piece | Where | What it does |
|---|---|---|
| Adapter interfaces | `adapters.py` | `ERPAdapter`, `MarketplaceAdapter`, `ShippingAdapter`, `MessagingAdapter` (SMS / WhatsApp / Telegram). `register_adapter(kind, obj)` plugs in a connector; `get_adapter(kind)` returns it or the Null one. |
| Versioning | adapter class name | A second API version of a vendor is a second class (`Vendor...V2`) registered instead of the first; the platform code does not change. |
| External ids | table `external_ids` | `(system, entity, internal_id) <-> external_id`. `set_external_id`, `get_external_id`, `find_internal_id`. The Bitrix24 deal id is saved here as well as in `orders.crm_deal_id`. |
| Events | `events.py` | `emit(db, "OrderPaid", order)` queues a job; delivered only if an adapter that listens is registered. Today: `OrderPaid`/`OrderCancelled` -> ERP `push_order`. |
| Job queue | `app/services/jobs.py`, `python -m app.tasks.worker` | Retries with backoff (1/5/15/30/60 min), dead-letter queue, admin retry. Failure of one integration never blocks checkout: it only fails its own job. |
| Call log | `integration_logs` + `/admin/integration-logs` | Every outbound CRM call: status, attempts, duration, dead letters, manual retry. |
| Health / alerts | `/admin/integration-logs/health`, `python -m app.tasks.check_alerts` | HEALTHY / DEGRADED / FAILED; emails dead letters, backlog, sync lag, payment-failure spikes, dead jobs. |
| Order documents | `order_documents`, `app/routers/order_documents.py` | Invoices / receipts / shipping / return documents, private storage (`DOCUMENTS_DIR`), 5-minute signed download links, voiding. |

## Inbound webhooks

`POST /api/v1/integrations/{provider}/webhook` (provider must have a secret in `WEBHOOK_SECRETS`, a JSON object
`{"erp": "long-random-secret"}`).

Headers the sender must send:

| Header | Value |
|---|---|
| `X-Maru-Timestamp` | unix time in seconds; rejected when more than 5 minutes off |
| `X-Maru-Signature` | hex `HMAC-SHA256(secret, "<timestamp>.<raw body>")` |
| `X-Maru-Event-Id` | unique id of the event (max 120 chars); a repeat is answered `{"status":"duplicate"}` and not processed again |

Answers: `202 {"status":"accepted"}`, `401` bad/stale signature, `404` unknown provider, `400` no event id,
`413` body over 1 MB, `429` rate limited (300/min per IP). The body is queued as job `webhook.received`; a
connector registers a handler for it (`@job_handler`) to do the real work. Timeout expected from the sender: 10 s.

## Order documents API

| Call | Who | Notes |
|---|---|---|
| `POST /admin/orders/{id}/documents` (multipart: `file`, `doc_type`, `external_id?`) | Sales manager+ | PDF / JPEG / PNG, 10 MB, content checked. `doc_type`: invoice, fiscal_receipt, shipping_document, return_document, other |
| `POST /admin/orders/{id}/documents/{doc}/void` | Sales manager+ | hides it from the customer |
| `GET /orders/{id}/documents` | order owner (login or `X-Order-Token`) | metadata only |
| `POST /orders/{id}/documents/{doc}/link` | order owner | returns a 5-minute signed URL |
| `GET /documents/download?token=` | anyone with the link | `Cache-Control: private, no-store`, `X-Robots-Tag: noindex` |

## Field mapping (PRD §79)

Mappings are written when a connector is written, in this form, and kept in this file:

| MARU field | Transformation | External field |
|---|---|---|
| `skus.sku_code` | as is | (ERP item code - to be confirmed with the ERP owner) |
| `orders.order_number` | as is | (ERP order number) |
| `orders.total_amount` + `orders.currency` | decimal string, ISO 4217 | (ERP amount / currency) |
| `orders.phone` | already E.164 shaped (digits, optional `+`) | (ERP phone) |
| `orders.created_at` | UTC, ISO 8601 | (ERP date) |

Bitrix24 (the only connector that exists) maps in `app/services/crm/bitrix24.py`: order -> deal
(`TITLE`, `OPPORTUNITY`, `CURRENCY_ID`, `COMMENTS`, contact), quote -> lead.

## Normalisation (PRD §80)

Currency ISO 4217 (`USD`, `UZS`...), country names as entered/selected, language `ru`/`uz`/`en`, phones digits with
optional `+` (checkout, addresses, quotes, accounts), timestamps stored UTC.

## Not built (needs a vendor, documents or credentials)

ERP/1C connector, Uzum / marketplace connector, SMS / WhatsApp / Telegram providers, GA4 / Meta server-side
forwarding. Each has its interface and Null adapter; see `PRD.md` build status for the exact reasons.

## Test environments (PRD §91-92)

Tests run on SQLite with fake data and no network (`tests/conftest.py` blanks SMTP). Keep sandbox credentials in a
separate `.env` from production credentials; never copy a production `.env` to a development machine.

## Web push (PRD TZ1 §38-39)

Needs `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` in `.env` (`python scripts/generate_vapid.py` makes them; never change them
after launch). Customers opt in on their account page; `/sw.js` is the service worker (serve it with `Cache-Control: no-cache`, see
`deploy/nginx.conf.example`). Pushed: order created / status changed / shipment updated, and abandoned carts. A subscription the push service
reports gone (404/410) is deleted. iPhones only get web push after the site is added to the home screen. Not tested against real browsers.

## Remarketing data and consent

Server events carry product ids (`items`) so GA4 / Meta audiences can be built. They are forwarded to GA4 / Meta only when the visitor accepted
analytics in the cookie banner: the storefront sends `X-Analytics-Consent: 1`, orders remember it (`orders.analytics_consent`) so a payment
callback later still honours it. The first-party `analytics_events` table is written regardless.

## Markets and loyalty

`products.sold_in_countries` / `hidden_in_countries` (country names, any case) limit where a product is shown and ordered; the storefront
passes the delivery country the visitor picked (`?country=`, cart `market_country`), checkout refuses a product not sold in the delivery
country. Loyalty: see `app/services/loyalty.py` (rules in its docstring); settings are edited in Admin > Loyalty.
