"""Small TTL cache for rarely-changing public reads (PRD ТЗ№3 §87: categories, site settings,
exchange rates). Uses Redis when REDIS_URL is set (shared by all workers), otherwise process memory.

Invalidation is automatic: any committed change to a table listed in TABLE_NAMESPACES drops that
namespace, so no admin route has to remember to do it. With in-process memory and several uvicorn
workers another worker only notices after the TTL - which is why more than one worker needs Redis
(already required for rate limiting). A Redis failure just means "compute it again"."""

import json
import logging
import time
from typing import Any, Callable

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.config import settings
from app.core.rate_limit import _get_redis_client

logger = logging.getLogger("maru.cache")

TABLE_NAMESPACES = {
    "categories": "categories",
    "category_translations": "categories",
    "site_settings": "site",
    "site_settings_translations": "site",
    "exchange_rates": "fx",
}

_memory: dict[str, tuple[float, str]] = {}
_versions: dict[str, int] = {}


def _version(ns: str) -> int:
    client = _get_redis_client()
    if client is not None:
        try:
            raw = client.get(f"maru:cachev:{ns}")
            return int(raw) if raw else 0
        except Exception:  # noqa: BLE001
            logger.warning("Redis cache version lookup failed")
    return _versions.get(ns, 0)


def get_or_set(ns: str, key: str, ttl: int, compute: Callable[[], Any]) -> Any:
    """Returns the JSON-compatible value of compute(), cached for `ttl` seconds."""
    if ttl <= 0 or not settings.CACHE_ENABLED:
        return compute()
    full = f"maru:cache:{ns}:{_version(ns)}:{key}"
    client = _get_redis_client()
    if client is not None:
        try:
            hit = client.get(full)
            if hit is not None:
                return json.loads(hit)
        except Exception:  # noqa: BLE001
            logger.warning("Redis cache read failed")
    else:
        hit = _memory.get(full)
        if hit and hit[0] > time.monotonic():
            return json.loads(hit[1])
    value = compute()
    payload = json.dumps(value, default=str)
    if client is not None:
        try:
            client.setex(full, ttl, payload)
        except Exception:  # noqa: BLE001
            logger.warning("Redis cache write failed")
    else:
        _memory[full] = (time.monotonic() + ttl, payload)
    return value


def invalidate(ns: str) -> None:
    _versions[ns] = _versions.get(ns, 0) + 1
    for k in [k for k in _memory if k.startswith(f"maru:cache:{ns}:")]:
        _memory.pop(k, None)
    client = _get_redis_client()
    if client is not None:
        try:
            client.incr(f"maru:cachev:{ns}")
        except Exception:  # noqa: BLE001
            logger.warning("Redis cache invalidation failed")


def clear() -> None:
    _memory.clear()
    _versions.clear()


@event.listens_for(Session, "after_flush")
def _remember_touched(session: Session, _ctx) -> None:
    touched = session.info.setdefault("cache_ns", set())
    for obj in list(session.new) + list(session.dirty) + list(session.deleted):
        ns = TABLE_NAMESPACES.get(getattr(obj, "__tablename__", ""))
        if ns:
            touched.add(ns)


@event.listens_for(Session, "after_commit")
def _invalidate_touched(session: Session) -> None:
    for ns in session.info.pop("cache_ns", ()):
        invalidate(ns)


@event.listens_for(Session, "after_rollback")
def _forget_touched(session: Session) -> None:
    session.info.pop("cache_ns", None)
