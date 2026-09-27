import logging
import time
import uuid
from collections import defaultdict, deque

import redis
from fastapi import HTTPException, Request, status

from app.config import settings

logger = logging.getLogger("maru.rate_limit")

_hits: dict[str, deque] = defaultdict(deque)

_redis_client: "redis.Redis | None" = None
_redis_warned = False


def _get_redis_client() -> "redis.Redis | None":
    """Lazily builds a shared Redis client from settings.REDIS_URL. Returns
    None (falling back to in-process limiting) if REDIS_URL isn't set, or if
    Redis is unreachable — a down rate-limiter must never take the API down
    with it."""
    global _redis_client, _redis_warned
    if not settings.REDIS_URL:
        return None
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=2)
    return _redis_client


def _redis_allow(client: "redis.Redis", key: str, limit: int, window_seconds: int) -> bool:
    """Sliding window over a Redis sorted set (PRD ТЗ№3 §80): each hit is a
    member scored by its own timestamp; members older than the window are
    trimmed before counting, so the count always reflects the last
    `window_seconds`, not a fixed bucket. Same semantics as the in-process
    deque version below, just shared across workers/processes."""
    now = time.time()
    pipe = client.pipeline()
    pipe.zremrangebyscore(key, 0, now - window_seconds)
    pipe.zcard(key)
    _, count = pipe.execute()
    if count >= limit:
        return False
    pipe = client.pipeline()
    pipe.zadd(key, {f"{now}:{uuid.uuid4().hex}": now})
    pipe.expire(key, window_seconds + 1)
    pipe.execute()
    return True


def _memory_allow(key: str, limit: int, window_seconds: int) -> bool:
    now = time.monotonic()
    hits = _hits[key]
    while hits and now - hits[0] > window_seconds:
        hits.popleft()
    if len(hits) >= limit:
        return False
    hits.append(now)
    return True


def rate_limit(name: str, limit: int, window_seconds: int):
    """Per-client-IP sliding-window limiter (PRD ТЗ№3 §80). Uses Redis when
    REDIS_URL is configured (required once more than one worker process is
    running — see TODO.md), otherwise falls back to in-process memory."""

    def dependency(request: Request) -> None:
        global _redis_warned
        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{name}:{client_ip}"

        redis_client = _get_redis_client()
        if redis_client is not None:
            try:
                allowed = _redis_allow(redis_client, key, limit, window_seconds)
            except redis.RedisError:
                if not _redis_warned:
                    logger.warning("Redis unavailable for rate limiting; falling back to in-process memory", exc_info=True)
                    _redis_warned = True
                allowed = _memory_allow(key, limit, window_seconds)
        else:
            allowed = _memory_allow(key, limit, window_seconds)

        if not allowed:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests, try again later")

    return dependency
