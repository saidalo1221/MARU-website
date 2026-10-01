# MARU operations runbook

None of this has been run on the real server (no access from the dev
machine). Treat every step as "verify on staging first".

## Scheduled jobs (cron)
| Job | Command | Suggested schedule |
|---|---|---|
| Expire unpaid reservations | `python -m app.tasks.expire_reservations` | every 5 min |
| Retry failed CRM pushes | `python -m app.tasks.retry_integrations` | every 10 min |
| Sync exchange rates | `python -m app.tasks.sync_exchange_rates` | daily |
| Back-in-stock emails | `python -m app.tasks.notify_back_in_stock` | every 10-15 min |
| Alerts (dead-letter / stuck integrations / payment-failure spike; needs `ALERT_EMAIL`, thresholds `ALERT_*`; same alert not repeated within `ALERT_COOLDOWN_MINUTES`) | `python -m app.tasks.check_alerts` | every 10 min |
| Stock drift report | `python -m app.tasks.reconcile_stock` (add `--fix` only after reading the report; exit 1 = mismatches found; also emails `ALERT_EMAIL` if set) | nightly |
| Database + uploads backup | `scripts/backup_db.sh` | daily, 02:15 |
| Background jobs (queued emails, webhooks; only needed when `JOBS_ASYNC=true`) | `python -m app.tasks.worker --once`, or run the `deploy/maru-worker.service` unit instead of cron | every minute (cron) / always on (systemd) |

Run each from the project root with the production `.env` loaded.

## Deployment files (`deploy/`, none tested on a real server)
- `nginx.conf.example` + `nginx-security-headers.conf`: one-domain site, HTTPS redirect, API and
  uploads proxied, SPA fallback, frontend security headers and a CSP written for Stripe, PayPal,
  OpenStreetMap, YouTube and ipapi.co. Start with `Content-Security-Policy-Report-Only`.
- `maru-backend.service`: systemd unit. More than one worker requires `REDIS_URL`.
- `crontab.example`: every scheduled job in one place.

## Logs and error tracking
Set `LOG_FORMAT=json` for one JSON object per line (time, level, logger, request_id, message,
exception). Optional Sentry: `pip install sentry-sdk`, then set `SENTRY_DSN`; events carry no
IPs or user details (`send_default_pii=False`). With the nginx example, the API's request id is
nginx's `$request_id`, so the access log and application log share it.

## Request ids
Every response carries `X-Request-ID` (a valid incoming one from the proxy is kept) and every log
line is tagged `[request-id]`. Ask a customer for the id from a failed request (browser dev tools, Network tab) and grep the logs.

## Backups
`scripts/backup_db.sh` writes `db-<stamp>.sql.gz` (consistent InnoDB snapshot
via `--single-transaction`) and `uploads-<stamp>.tar.gz`, then deletes files
older than `KEEP_DAYS` (default 14). Uploads are local disk, so they need the
tarball too. Copy the backup directory **off the server** (another host or
object storage) - a backup on the same disk does not survive the disk.

Setup: create `~/.maru-backup.cnf` (`chmod 600`) with a `[client]` section
holding the DB user and password; confirm the DB user has `SELECT`,
`LOCK TABLES`, `SHOW VIEW`, `TRIGGER` on the database.

## Restore (rehearse quarterly on staging)
1. Stop the app (or put the proxy in maintenance mode).
2. Restore into an empty database:
   ```
   mysql -e "DROP DATABASE IF EXISTS maruplast_restore; CREATE DATABASE maruplast_restore CHARACTER SET utf8mb4"
   gunzip -c db-<stamp>.sql.gz | mysql maruplast_restore
   ```
   Check row counts (`orders`, `users`, `skus`) against production first.
3. Only then swap: restore over `maruplast` the same way, or point
   `DATABASE_URL` at the restored copy.
4. Restore uploads: `tar -xzf uploads-<stamp>.tar.gz -C app/static/uploads`.
5. Start the app and place a test order.

## Container
`docker build -t maru-backend .` then run with the production `.env`
(`--env-file`), port 8000 behind the reverse proxy, and a volume on
`/srv/maru/app/static/uploads`. Set `FORWARDED_ALLOW_IPS=<proxy ip>`.
The Dockerfile has **not** been built (no Docker on the dev machine).

## Reverse proxy checklist
- Route `/api/` and `/static/` and `/sitemap.xml` to the backend; everything
  else to the built frontend (`frontend/dist`).
- The API sets its own security headers. The proxy must add the same ones to
  the frontend's static responses (`X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Referrer-Policy`, HSTS) plus a Content-Security-
  Policy written for the React app (it loads Leaflet tiles and, if enabled,
  Stripe/PayPal scripts, so it cannot be copied from the API's `default-src
  'none'`).
- Swagger UI / `openapi.json` are off unless `ENABLE_DOCS=true`. Leave it off
  in production.

## CI
`.github/workflows/ci.yml` runs the backend tests on Python 3.9 (production's
version) and builds the frontend on every push and pull request. The first run
on GitHub is also the first real Python 3.9 test run - check it.

## Disaster recovery targets (PRD ТЗ№3 §83) - APPROVED by the owner

| Target | Proposed | How it is met today |
|---|---|---|
| RPO (data we can afford to lose) | 24 h now; 1 h once binary logging is enabled | nightly `scripts/backup_db.sh`; for 1 h enable MariaDB binlog and ship it hourly |
| RTO (time to be back) | 4 h | restore procedure above, rehearsed quarterly on staging |

Approved by the owner on 2026-10-01: RPO 24 h at launch (1 h once binary logging is enabled and shipped hourly), RTO 4 h. Turning on the binary log is a deployment task; the code needs no change.

## Environments and release flow (PRD ТЗ№3 §94-100)

Development (a laptop, SQLite) -> CI (GitHub Actions: lint, tests, build, dependency scan) -> Staging (a second
UzCloud instance with its own database and sandbox keys; **not provisioned yet**) -> Production. Merge to `main` only
after the CI run is green. Release = tag + `git pull` on the server + run any new `app/migration_*.sql` by hand
(schema changes only ever come from those versioned files) + restart `maru-backend` (and `maru-worker`). Rollback = check
out the previous tag and restart; migrations are additive, so they need no undoing. Deploy to staging and click through
checkout before every production release.
