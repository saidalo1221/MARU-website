# Putting MARU online on Arsenal D (webname.uz)

Nothing here has been run on a real server yet (see the notes in `OPS_RUNBOOK.md`). Do each step on the real server
and check it before moving on. Replace `shop.example.uz` with your domain everywhere.

## 0. What to buy

MARU is a Python backend with MariaDB, a background worker and cron jobs, plus a static storefront. That needs a
**VPS with root (SSH) access**. Ordinary shared hosting (DirectAdmin only, no SSH or no way to keep a program running)
can host the storefront files but not the backend, so the shop would load and show nothing.

Ask Arsenal D before paying:
1. VPS with root access, Ubuntu 22.04 (or Debian 12), at least 2 GB RAM, 20 GB disk?
2. Python 3.9 or newer, MariaDB 10.5 or newer, Redis and nginx allowed?
3. A real public IPv4 address, and ports 80 and 443 open?
4. If the VPS comes with a DirectAdmin panel: can it be turned off, or can nginx be pointed at the app?
   (Simplest is a plain server with no panel.)

## 1. Domain and DNS

1. Register the `.uz` domain at webname.uz.
2. In its DNS settings add an **A record**: `shop.example.uz` (and `www`) -> the server's IP address.
   It can take minutes to a few hours to spread.

## 2. Prepare the server (as root over SSH)

```bash
apt update && apt install -y python3 python3-venv python3-pip nginx mariadb-server redis-server certbot python3-certbot-nginx git
adduser --system --group --home /srv/maru maru
```

## 3. Database

```sql
-- mysql -u root
CREATE DATABASE maruplast CHARACTER SET utf8mb4;
CREATE USER 'maruplast'@'localhost' IDENTIFIED BY '<a new strong password>';
GRANT ALL PRIVILEGES ON maruplast.* TO 'maruplast'@'localhost';
```

Then create the tables with the SQL files in the order `MARIADB_PREFLIGHT.md` gives (`app/schema_mariadb.sql`, then the
`app/migration_*.sql` files). Nothing has ever run on MariaDB, so do this once and read every error.

## 4. The backend

```bash
git clone <your repo address> /srv/maru        # a private repo needs a deploy key; or copy the folder with scp
cd /srv/maru && python3 -m venv venv && venv/bin/pip install -r requirements.txt
mkdir -p app/static/uploads /var/log/maru && chown -R maru /srv/maru/app/static /var/log/maru
```

Create `/srv/maru/.env` (never commit it):

```
ENVIRONMENT=production
SECRET_KEY=<python3 -c "import secrets; print(secrets.token_urlsafe(48))">
DATABASE_URL=mysql+pymysql://maruplast:<password>@localhost:3306/maruplast
FRONTEND_URL=https://shop.example.uz
BACKEND_URL=https://shop.example.uz
CORS_ORIGINS=https://shop.example.uz
REDIS_URL=redis://127.0.0.1:6379/0
SMTP_HOST=...  SMTP_PORT=...  SMTP_USER=...  SMTP_PASSWORD=...  SMTP_FROM_EMAIL=...
TELEGRAM_BOT_TOKEN=...  TELEGRAM_ADMIN_CHAT_ID=...  TELEGRAM_ALERT_LANG=ru
```

Do not set `CORS_ORIGIN_REGEX` or `ENABLE_DOCS` in production. Payment keys go in the same file once you have them
(`LAUNCH_CHECKLIST.md`, section 3). Then:

```bash
cd /srv/maru && venv/bin/python scripts/launch_preflight.py --smtp     # fix every FAIL
venv/bin/python scripts/create_admin.py you@example.uz                 # your admin account
cp deploy/maru-backend.service /etc/systemd/system/ && systemctl daemon-reload && systemctl enable --now maru-backend
# only if JOBS_ASYNC=true: the same with deploy/maru-worker.service
crontab -u maru deploy/crontab.example                                  # the scheduled jobs
```

## 5. The storefront (build on your own computer, then upload)

```bash
cd frontend
VITE_API_BASE_URL=https://shop.example.uz/api/v1 npm run build
scp -r dist root@<server ip>:/srv/maru/frontend/
```

The API address is baked into the build, so rebuild it whenever the domain changes.

## 6. nginx and https

```bash
cp deploy/nginx.conf.example /etc/nginx/sites-available/maru     # replace shop.example.com with your domain
cp deploy/nginx-security-headers.conf /etc/nginx/snippets/maru-security-headers.conf
ln -s /etc/nginx/sites-available/maru /etc/nginx/sites-enabled/ && nginx -t
certbot --nginx -d shop.example.uz -d www.shop.example.uz          # free https certificate, renews itself
systemctl reload nginx
```

(Run certbot before the `ssl_certificate` lines are active, or use certbot's own setup, as `nginx -t` fails without
the certificate files.)

## 7. After it is up

1. Open the site, sign in at `/admin` (the code arrives by e-mail), upload real products and photos, then run
   `python scripts/remove_demo_data.py` (add `--apply` to delete the demo products).
2. Set up a payment provider and register its webhook addresses (`LAUNCH_CHECKLIST.md`, section 3).
3. Place a small test order and check the Telegram alert and the e-mails arrive.
4. Turn on the daily backup (`scripts/backup_db.sh`, see `OPS_RUNBOOK.md`) and test a restore once.
5. Submit `https://shop.example.uz/sitemap.xml` in Google Search Console.
6. Rotate the credentials that were pasted in chat (Telegram, GA4, Meta, Gmail app password).

## Updating later

```bash
cd /srv/maru && git pull && venv/bin/pip install -r requirements.txt && systemctl restart maru-backend
# for storefront changes: rebuild locally and scp the dist folder again
```
