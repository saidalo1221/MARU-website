"""Per-request correlation id (PRD ТЗ№3 §92 logging). Every response carries
`X-Request-ID`, and every log line emitted while handling the request is
tagged with it, so one customer report can be traced through the logs."""

import logging
import re
from typing import Optional
from contextvars import ContextVar
from uuid import uuid4

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
# The caller's address for the current request (audit log, PRD ТЗ№3 §81). Behind a reverse proxy
# this is the real client once uvicorn runs with --proxy-headers (see OPS_RUNBOOK.md).
client_ip_var: ContextVar[Optional[str]] = ContextVar("client_ip", default=None)

# Did the visitor agree to analytics / advertising measurement (the cookie banner's "analytics" choice)? The
# storefront sends `X-Ads-Consent: 1` only then; ad platforms (GA4, Meta) get events only when it is set.
ads_consent_var: ContextVar[bool] = ContextVar("ads_consent", default=False)

# Accept an id from the proxy/client only if it is short and boring; anything
# else (log-injection attempts, huge values) is replaced with a fresh one.
_VALID_ID = re.compile(r"[A-Za-z0-9._\-]{8,64}")


def new_request_id(incoming: Optional[str] = None) -> str:
    if incoming and _VALID_ID.fullmatch(incoming):
        return incoming
    return uuid4().hex


def install_log_record_factory() -> None:
    """Adds `%(request_id)s` to every log record, whatever handler formats it."""
    previous = logging.getLogRecordFactory()

    def factory(*args, **kwargs):
        record = previous(*args, **kwargs)
        record.request_id = request_id_var.get()
        return record

    logging.setLogRecordFactory(factory)
