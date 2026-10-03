"""Logging and optional error tracking setup, driven by settings (.env):

  LOG_LEVEL   INFO (default), DEBUG, WARNING ...
  LOG_FORMAT  "text" (default, readable) or "json" (one object per line, for log shippers)
  SENTRY_DSN  optional; needs `pip install sentry-sdk` (not in requirements.txt on purpose)
"""

import json
import logging
from datetime import datetime, timezone

from app.config import settings

TEXT_FORMAT = "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"
logger = logging.getLogger("maru.logging")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


def configure_logging() -> None:
    """Only touches the root logger if nothing configured it already (uvicorn
    configures just its own loggers), so importing the app in tests or under
    another runner does not override their setup."""
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter() if settings.LOG_FORMAT.lower() == "json" else logging.Formatter(TEXT_FORMAT))
    root.addHandler(handler)
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))


def init_error_tracking() -> bool:
    """Starts Sentry when SENTRY_DSN is set. Returns whether it is active; a
    missing package or bad DSN is logged, never raised - monitoring must not
    stop the shop from starting."""
    if not settings.SENTRY_DSN:
        return False
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            send_default_pii=False,  # no IPs, cookies or user details attached to events
            traces_sample_rate=0.0,
        )
    except ImportError:
        logger.warning("SENTRY_DSN is set but sentry-sdk is not installed (pip install sentry-sdk); error tracking is off")
        return False
    except Exception:
        logger.exception("Could not initialise Sentry; error tracking is off")
        return False
    return True
