"""Launch preflight: reads the same settings the backend uses (.env + environment) and reports
PASS / WARN / FAIL for everything that has to be right before real customers use the shop.
Secrets are never printed.

    python scripts/launch_preflight.py            # config checks, database connection
    python scripts/launch_preflight.py --smtp     # also logs in to the SMTP server (sends nothing)

Exit code 1 when anything FAILs, so it can also run in CI / before a deploy.
"""
import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402

results = []


def add(level, name, detail=""):
    results.append((level, name, detail))


def is_local(url):
    host = (urlparse(url or "").hostname or "").lower()
    return host in ("localhost", "127.0.0.1", "::1", "0.0.0.0") or host.endswith(".local")


# --------------------------------------------------------------------------------- database
def check_database():
    url = settings.DATABASE_URL
    parsed = urlparse(url.replace("mysql+pymysql", "mysql", 1))
    where = "%s@%s:%s/%s" % (parsed.username, parsed.hostname, parsed.port or "", (parsed.path or "").lstrip("/"))
    if url.startswith("sqlite"):
        add("FAIL", "Database", "SQLite is the local test database. Production needs MariaDB (mysql+pymysql://user:password@host:3306/db).")
        return
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 8})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        add("PASS", "Database connection", where)
    except Exception as exc:  # noqa: BLE001
        code = getattr(getattr(exc, "orig", None), "args", [None])[0]
        if code == 1045:
            why = "MariaDB refused the user or password (error 1045). Check the user name and password in DATABASE_URL."
        elif code == 1049:
            why = "The database does not exist (error 1049). Create it or fix the name."
        elif code in (2002, 2003):
            why = "Cannot reach the database server (error %s). Is MariaDB running, and is the host/port right?" % code
        else:
            why = "%s: %s" % (type(exc).__name__, str(exc).split("\n")[0][:160])
        add("FAIL", "Database connection", "%s  [%s]" % (why, where))


# ---------------------------------------------------------------------------------- the rest
def check_config():
    key = settings.SECRET_KEY or ""
    if len(key) < 32 or key.lower() in ("changeme", "secret", "dev", "change-me"):
        add("FAIL", "SECRET_KEY", "Too short or a placeholder. Use at least 32 random characters (python -c \"import secrets; print(secrets.token_urlsafe(48))\").")
    else:
        add("PASS", "SECRET_KEY", "%d characters" % len(key))

    add("PASS" if settings.ENVIRONMENT == "production" else "WARN", "ENVIRONMENT", settings.ENVIRONMENT)
    add("FAIL" if settings.ENABLE_DOCS else "PASS", "API docs", "ENABLE_DOCS is on: Swagger would publish every admin route" if settings.ENABLE_DOCS else "off")

    for name, value in (("FRONTEND_URL", settings.FRONTEND_URL), ("BACKEND_URL", settings.BACKEND_URL)):
        if is_local(value):
            add("FAIL", name, "%s points at this computer. Set the public https address (links in e-mails and image URLs use it)." % value)
        elif not value.startswith("https://"):
            add("WARN", name, "%s is not https" % value)
        else:
            add("PASS", name, value)

    local_origins = [o for o in settings.cors_origins if is_local(o)]
    if local_origins:
        add("WARN", "CORS_ORIGINS", "still lists local addresses: %s. Replace with the public site address." % ", ".join(local_origins))
    elif not settings.cors_origins:
        add("FAIL", "CORS_ORIGINS", "empty: the browser could not call the API")
    else:
        add("PASS", "CORS_ORIGINS", ", ".join(settings.cors_origins))
    if settings.CORS_ORIGIN_REGEX:
        add("FAIL", "CORS_ORIGIN_REGEX", "set. It is for local development only; remove it in production.")


def check_mail(do_login):
    if not (settings.SMTP_HOST and settings.SMTP_FROM_EMAIL):
        add("FAIL", "E-mail (SMTP)", "SMTP_HOST / SMTP_FROM_EMAIL missing: no reset links, login codes or order e-mails will arrive.")
        return
    if "gmail.com" in settings.SMTP_HOST:
        add("WARN", "E-mail provider", "Gmail allows about 500 messages a day. Use a transactional mail service for real volume.")
    if not do_login:
        add("PASS", "E-mail (SMTP) settings", "%s:%s as %s (run with --smtp to test the login)" % (settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_FROM_EMAIL))
        return
    import smtplib

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            server.ehlo()
            if settings.SMTP_USE_TLS:
                server.starttls()
                server.ehlo()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        add("PASS", "E-mail (SMTP) login", "accepted by %s" % settings.SMTP_HOST)
    except Exception as exc:  # noqa: BLE001
        add("FAIL", "E-mail (SMTP) login", "%s: %s" % (type(exc).__name__, str(exc)[:140]))


def check_payments():
    needs = {
        "Payme": ["PAYME_MERCHANT_ID", "PAYME_KEY"],
        "Click": ["CLICK_SERVICE_ID", "CLICK_MERCHANT_ID", "CLICK_SECRET_KEY"],
        "Stripe": ["STRIPE_SECRET_KEY"],  # the browser also needs VITE_STRIPE_PUBLISHABLE_KEY at build time
        "PayPal": ["PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET"],
    }
    ready = []
    for provider, names in needs.items():
        missing = [n for n in names if not getattr(settings, n, None)]
        if not missing:
            ready.append(provider)
        else:
            add("WARN", "Payment: %s" % provider, "missing %s" % ", ".join(missing))
    if ready:
        add("PASS", "Payments", "ready: %s" % ", ".join(ready))
    else:
        add("FAIL", "Payments", "No provider is configured, so checkout cannot take an order. Set up at least Payme or Click (Uzbekistan).")
    if "sandbox" in (settings.PAYPAL_API_BASE or "") and settings.PAYPAL_CLIENT_ID:
        add("FAIL", "PayPal mode", "PAYPAL_API_BASE is the sandbox; switch to https://api-m.paypal.com for live payments.")


def check_extras():
    add("PASS" if settings.REDIS_URL else "WARN", "Redis", "set" if settings.REDIS_URL else "REDIS_URL missing: rate limits and caching run per process only")
    if settings.JOBS_ASYNC:
        add("WARN", "Background jobs", "JOBS_ASYNC is on: `python -m app.tasks.worker` must be running (see deploy/maru-worker.service)")
    add("FAIL" if settings.META_TEST_EVENT_CODE else "PASS", "Meta test code", "META_TEST_EVENT_CODE is set: live events would only appear under Test events" if settings.META_TEST_EVENT_CODE else "empty")
    add("PASS" if (settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY) else "WARN", "Web push keys", "set" if settings.VAPID_PUBLIC_KEY else "missing (scripts/generate_vapid.py); keep them forever once chosen")
    add("PASS" if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_ADMIN_CHAT_ID else "WARN", "Telegram staff alerts", "configured" if settings.TELEGRAM_BOT_TOKEN else "not configured")
    add("PASS" if settings.GA4_MEASUREMENT_ID else "WARN", "Google Analytics 4", "configured" if settings.GA4_MEASUREMENT_ID else "not configured")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--smtp", action="store_true", help="also log in to the SMTP server")
    args = ap.parse_args()

    check_database()
    check_config()
    check_mail(args.smtp)
    check_payments()
    check_extras()

    marks = {"PASS": "[ ok ]", "WARN": "[warn]", "FAIL": "[FAIL]"}
    for level, name, detail in results:
        print("%s %-26s %s" % (marks[level], name, detail))
    fails = sum(1 for r in results if r[0] == "FAIL")
    warns = sum(1 for r in results if r[0] == "WARN")
    print("\n%d failing, %d warnings, %d passing" % (fails, warns, len(results) - fails - warns))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
