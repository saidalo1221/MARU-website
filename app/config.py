from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 600
    ENVIRONMENT: str = "production"
    # Comma-separated browser origins. Set this to the deployed frontend URL
    # in production; localhost values make a separate Vite dev server work.
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    # Swagger UI / ReDoc / openapi.json publish every admin route. Off unless
    # explicitly enabled (set ENABLE_DOCS=true in a local .env).
    ENABLE_DOCS: bool = False
    # Logging (app/core/logging_config.py): "text" or "json"; optional Sentry DSN.
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"
    SENTRY_DSN: Optional[str] = None

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Payment providers (PRD section 13) — all optional; a gateway raises
    # PaymentConfigError at call time if its settings aren't filled in yet.
    PAYME_MERCHANT_ID: Optional[str] = None
    PAYME_KEY: Optional[str] = None
    # Payme's test/sandbox merchant endpoint is checkout.test.paycom.uz; production is checkout.paycom.uz.
    PAYME_CHECKOUT_URL: str = "https://checkout.paycom.uz"

    CLICK_SERVICE_ID: Optional[str] = None
    CLICK_MERCHANT_ID: Optional[str] = None
    CLICK_SECRET_KEY: Optional[str] = None

    # Uzum Pay intentionally has no settings yet: merchant API documentation
    # and sandbox credentials must be supplied before an integration is built.

    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    PAYPAL_CLIENT_ID: Optional[str] = None
    PAYPAL_CLIENT_SECRET: Optional[str] = None
    PAYPAL_API_BASE: str = "https://api-m.sandbox.paypal.com"  # switch to api-m.paypal.com for live

    # Base URL of the deployed frontend, used in password-reset links.
    FRONTEND_URL: str = "http://localhost:5173"

    # Base URL of this API itself, used to build absolute URLs for uploaded
    # files (admin_uploads.py) so they render correctly from the frontend's
    # origin, not just the API's.
    BACKEND_URL: str = "http://127.0.0.1:8000"

    # How long an unpaid order holds its stock reservation (PRD ТЗ№3 §19/§63)
    # before app/tasks/expire_reservations.py is allowed to release it.
    RESERVATION_TTL_MINUTES: int = 30

    # Cache (PRD ТЗ№3 §11). Also backs rate limiting (app/core/rate_limit.py)
    # so limits are shared across worker processes, not per-process memory.
    # Leave unset to keep the old in-process limiter for local dev without Redis.
    REDIS_URL: Optional[str] = None

    # Live FX feed (app/services/fx_provider.py) that populates the
    # admin-maintained ExchangeRate table (app/models/exchange_rate.py) — it
    # doesn't replace that table, it's just another way to fill it in,
    # exactly as that model's docstring anticipated. exchangerate-api.com's
    # free tier is 1,500 requests/month; sync on a daily schedule (see
    # app/tasks/sync_exchange_rates.py), never per-request, to stay well
    # under that with room to spare.
    EXCHANGERATE_API_KEY: Optional[str] = None
    EXCHANGERATE_API_BASE: str = "https://v6.exchangerate-api.com/v6"

    # CRM (PRD section 26).
    BITRIX24_WEBHOOK_URL: Optional[str] = None

    # Notifications (PRD section 38) — email only for now.
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_USE_TLS: bool = True
    # Where operational alerts (e.g. stock reconciliation mismatches) go.
    ALERT_EMAIL: Optional[str] = None
    # Thresholds for app/tasks/check_alerts.py (PRD ТЗ№4 §67).
    ALERT_PAYMENT_FAILURES: int = 5  # PAYMENT_FAILED orders within the last hour
    ALERT_RETRY_BACKLOG: int = 20  # integration calls waiting for a retry
    ALERT_SYNC_LAG_MINUTES: int = 60  # oldest unresolved integration failure
    ALERT_COOLDOWN_MINUTES: int = 360  # don't repeat the same alert sooner than this
    ALERT_JOB_BACKLOG_MINUTES: int = 30  # a due background job waiting this long raises an alert

    # Background jobs (PRD ТЗ№3 §88-89). With JOBS_ASYNC=false order emails are sent inside the
    # request (simple, fine for development); set it to true in production and run
    # `python -m app.tasks.worker` so checkout never waits for SMTP.
    # Private order documents (invoices, receipts). Empty = app/private_documents; on UzCloud point it
    # at a persistent volume outside the web root.
    DOCUMENTS_DIR: str = ""
    # Telegram bot (app/services/integrations/telegram.py). The token comes from @BotFather; keep it in .env only.
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = ""
    TELEGRAM_ADMIN_CHAT_ID: str = ""  # chat/group id that receives operational alerts
    # Google Analytics 4 Measurement Protocol (app/services/integrations/ga4.py). Keep the secret in .env only.
    GA4_MEASUREMENT_ID: str = ""
    GA4_API_SECRET: str = ""
    GA4_DEBUG: bool = False  # true = send to Google's validator instead of recording
    JOBS_ASYNC: bool = False
    # TTL cache for public categories / site settings / exchange rates (PRD ТЗ№03 §87). Writes invalidate it.
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 300
    JOB_MAX_ATTEMPTS: int = 5
    JOB_RETRY_BACKOFF_MINUTES: str = "1,5,15,30,60"  # delay before attempt 2, 3, 4, ...
    # Inbound webhooks (PRD ТЗ№4 §50-51): JSON object {"provider": "shared secret"}.
    WEBHOOK_SECRETS: str = ""


settings = Settings()
