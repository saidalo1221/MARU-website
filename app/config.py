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


settings = Settings()
