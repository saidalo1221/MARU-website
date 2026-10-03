# Launch checklist

Run `python scripts/launch_preflight.py --smtp` at any time. It reads the real `.env`, prints
PASS / WARN / FAIL for each item below (never a secret) and exits with 1 when something fails.
Last run (2026-10-02, on the development computer): 5 failing, 7 warnings. Everything that failed
needs information or accounts that only the owner has, so none of it could be filled in here.

## 1. Database (FAIL: access denied)

`.env` points at `mysql+pymysql://maru:...@localhost:3306/maruplast` and MariaDB answers
"access denied for user 'maru'" (error 1045). CLAUDE.md names the database user `maruplast`, so one of
the two is wrong. The local backend only runs because it is started with
`DATABASE_URL=sqlite:///./dev.db` on its command line; a plain restart would fail.

1. On the database server, as an administrator, create the user the documents say and give it the database:
   `CREATE USER 'maruplast'@'localhost' IDENTIFIED BY '<new strong password>';`
   `GRANT ALL PRIVILEGES ON maruplast.* TO 'maruplast'@'localhost'; FLUSH PRIVILEGES;`
2. Put the same user and password into `DATABASE_URL` in `.env`.
3. Re-run the preflight until "Database connection" passes.
4. Back up, then apply the SQL in the order listed in `MARIADB_PREFLIGHT.md` on a **copy** first.
   Nothing here has ever run on MariaDB.

## 2. Public addresses (FAIL)

| Setting | Now | Set to |
|---|---|---|
| `FRONTEND_URL` | `http://localhost:5173` | the public https address of the shop (used in every e-mail link) |
| `BACKEND_URL` | `http://127.0.0.1:8000` | the public https address of the API (used for uploaded image URLs) |
| `CORS_ORIGINS` | two localhost values | only the public shop address |
| `CORS_ORIGIN_REGEX` | local-development regex | delete the line (local use only) |
| frontend build: `VITE_API_BASE_URL` | local API | the public API address + `/api/v1`, set when running `npm run build` |

Images already uploaded keep the old `127.0.0.1` address in the database. After the real address is
known, re-upload them in the admin (they are placeholders anyway) or update the URLs.

## 3. Payments (FAIL: no provider configured)

Checkout needs at least one enabled provider; today all are marked "Merchant configuration is incomplete".
Each provider's own account, sandbox keys and contract are required, so this is blocked on the owner.

| Provider | Variables in `.env` | Notes |
|---|---|---|
| Payme | `PAYME_MERCHANT_ID`, `PAYME_KEY` | register the callback `https://<api>/api/v1/payments/payme/webhook` |
| Click | `CLICK_SERVICE_ID`, `CLICK_MERCHANT_ID`, `CLICK_SECRET_KEY` | register `https://<api>/api/v1/payments/click/webhook` |
| Stripe | `STRIPE_SECRET_KEY` and, at frontend build time, `VITE_STRIPE_PUBLISHABLE_KEY` | confirmed from the browser after payment |
| PayPal | `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_API_BASE=https://api-m.paypal.com`, and `VITE_PAYPAL_CLIENT_ID` at build time | the default base is the **sandbox**; live needs the line above |

Test every provider in its sandbox with a small order before enabling real money. Payme and Click only
appear for Uzbekistan deliveries by design. Uzum Pay is not built (no merchant documentation yet).

## 4. E-mail

SMTP login works (Gmail). Gmail allows about 500 messages a day, and mail "from" the same Gmail address
often lands in Spam. For launch use a transactional mail service (set `SMTP_*`), add SPF and DKIM for the
shop's domain, and use a `SMTP_FROM_EMAIL` on that domain. Login on a new device and password resets both
depend on this working.

## 5. Servers and jobs

- `REDIS_URL` (warning): shared rate limits and caching. Without it each process counts alone.
- Background worker and cron: `deploy/maru-worker.service`, `deploy/crontab.example`, `OPS_RUNBOOK.md`.
  If `JOBS_ASYNC=true` the worker must be running or e-mails and webhooks queue up.
- nginx rules (bot prerender, `/sw.js` no-cache) in `deploy/nginx.conf.example` have never run anywhere.

## 6. Clean the test data

`python scripts/remove_demo_data.py` previews (changes nothing); add `--apply` to delete the demo products,
the `gbgf` test product and their photos, and `--original-photos` to also remove the Commons photos from
the first two products. Orders are never touched. See `IMAGE_CREDITS.md`. Real product photos and the real
catalogue replace them. Cancel or delete leftover test orders in Admin > Orders.

## 7. Secrets

Rotate the Telegram, GA4 and Meta credentials that were pasted in chat (see START_HERE.md), and replace the
Gmail app password if it was shared. `.env` is git-ignored; keep it that way.
