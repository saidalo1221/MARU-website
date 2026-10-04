# Putting MARU online on DirectAdmin hosting (Arsenal D / webname.uz)

For a hosting account that has **Setup Python App**, **Terminal**, **phpMyAdmin** and **Cron jobs** in its panel and no
SSH or root access. (With a VPS, use `DEPLOY_ARSENALD.md` instead.) Nothing here has run on a real server before;
check every step. Assumed names: the shop is `maruplast.uz`, the API is `api.maruplast.uz`, the panel account is `maruuz`.
Change them everywhere if yours differ (and rebuild the storefront, see the end).

The two upload files (`storefront.zip`, `backend.zip`) are made by `python scripts/pack_upload.py` into `Desktop/maru-upload`.

## 1. Domains (Domain Setup)
1. `maruplast.uz` exists. Its web folder is `/domains/maruplast.uz/public_html`.
2. Add the subdomain `api` (so `api.maruplast.uz`). Leave **CGI off**: the Python app does not need it.
3. Turn on SSL for both (*Let's Encrypt* / free certificate in the domain's SSL page), then "force https".

## 2. Storefront
File Manager > `/domains/maruplast.uz/public_html` > Upload `storefront.zip` > select it > Extract. Its files
(`index.html`, `assets/`, `.htaccess`, ...) must sit directly in `public_html`, not in a sub-folder. Delete the zip.

## 3. Database
1. Panel > MySQL Management: create a database and a user (the panel adds the account prefix, e.g. `maruuz_shop`);
   note the exact names and the password.
2. phpMyAdmin: import `app/schema_mariadb.sql` first, then the `app/migration_*.sql` files in the order given in
   `MARIADB_PREFLIGHT.md`. Nothing has run on MariaDB before: read every error.

## 4. Backend
1. File Manager: in the home folder (`/home/maruuz`, **not** inside `domains/`) create the folder `maru-api`, upload
   `backend.zip` there and extract it. Open `env-template.txt`, fill it in, and save it as `.env` in `maru-api`.
2. Panel > Setup Python App > Create: Python **3.12**, application root `maru-api`, URL `api.maruplast.uz`,
   startup file `passenger_wsgi.py`, entry point `application`. Save.
3. On that app's page: under configuration files add `requirements-passenger.txt` and press *Run Pip Install*.
   Restart the app. (Disk is tight on a 2 GB plan: the packages need a few hundred MB.)
4. Terminal (or the app's "enter virtual environment" command), in `maru-api`: `python scripts/launch_preflight.py`
   and `python scripts/create_admin.py you@example.uz`.
5. Check `https://api.maruplast.uz/api/v1/site-settings` answers with JSON.

## 5. Scheduled jobs (Cron jobs)
Use the app's virtual environment's Python (the app page shows its path) and `cd /home/maruuz/maru-api` first:
every 5 min `python -m app.tasks.expire_reservations`, every minute `python -m app.tasks.worker --once` (only if
`JOBS_ASYNC=true`), hourly `python -m app.tasks.abandoned_carts`, and the rest from `deploy/crontab.example`.

## 6. After it is up
Open `https://maruplast.uz`, sign in at `/admin`, add real products, run `python scripts/remove_demo_data.py`, set up a
payment provider (`LAUNCH_CHECKLIST.md`), place a test order and check the Telegram alert, submit
`https://maruplast.uz/sitemap.xml` to Google Search Console, and rotate the credentials that were pasted in chat.

## Limits of this setup
No Redis-backed rate limits unless the panel's Redis feature is configured (set `REDIS_URL`), and no bot-preview
(rich link preview) rules, because those live in nginx. The storefront is built for one fixed API address:
`VITE_API_BASE_URL=https://api.maruplast.uz/api/v1 npm run build` in `frontend/`, then zip the contents of `dist/` together
with the `.htaccess` (single-page fallback and https redirect) into `storefront.zip`.
