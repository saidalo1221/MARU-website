"""Sliding-window rate limiting, both the in-process fallback and the Redis
path (PRD ТЗ№3 §80). Uses `fakeredis` in place of a real Redis server (no
Redis reachable from this dev environment — see TODO.md); `fakeredis` is a
test-only dependency, not in requirements.txt."""

import time

import app.config as config_module
import app.core.rate_limit as rate_limit_module


class _FakeRequest:
    def __init__(self, host):
        self.client = type("C", (), {"host": host})()


def test_in_process_fallback_blocks_after_limit():
    dependency = rate_limit_module.rate_limit("test_mem", 3, 60)
    request = _FakeRequest("1.2.3.4")
    for _ in range(3):
        dependency(request)

    try:
        dependency(request)
        assert False, "expected 429"
    except Exception as exc:
        assert exc.status_code == 429


def test_different_clients_have_independent_buckets():
    dependency = rate_limit_module.rate_limit("test_mem_2", 1, 60)
    dependency(_FakeRequest("1.1.1.1"))
    dependency(_FakeRequest("2.2.2.2"))  # does not raise


def test_redis_backed_limiter_via_fakeredis(monkeypatch):
    fakeredis = __import__("fakeredis")
    fake_client = fakeredis.FakeRedis()
    monkeypatch.setattr(rate_limit_module, "_redis_client", fake_client)
    monkeypatch.setattr(config_module.settings, "REDIS_URL", "redis://fake/0")

    dependency = rate_limit_module.rate_limit("test_redis", 2, 60)
    request = _FakeRequest("9.9.9.9")
    dependency(request)
    dependency(request)
    try:
        dependency(request)
        assert False, "expected 429"
    except Exception as exc:
        assert exc.status_code == 429


def test_redis_sliding_window_expires(monkeypatch):
    fakeredis = __import__("fakeredis")
    fake_client = fakeredis.FakeRedis()
    monkeypatch.setattr(rate_limit_module, "_redis_client", fake_client)
    monkeypatch.setattr(config_module.settings, "REDIS_URL", "redis://fake/0")

    dependency = rate_limit_module.rate_limit("test_redis_window", 1, 1)
    request = _FakeRequest("1.1.1.1")
    dependency(request)
    try:
        dependency(request)
        assert False, "expected immediate 429"
    except Exception:
        pass
    time.sleep(1.2)
    dependency(request)  # allowed again


def test_unreachable_redis_falls_back_to_memory(monkeypatch):
    """Configured but unreachable Redis must degrade gracefully, not break
    the request (PRD §78's isolation principle applies here too)."""
    monkeypatch.setattr(config_module.settings, "REDIS_URL", "redis://127.0.0.1:1/0")
    monkeypatch.setattr(rate_limit_module, "_redis_client", None)

    dependency = rate_limit_module.rate_limit("test_unreachable", 2, 60)
    request = _FakeRequest("3.3.3.3")
    dependency(request)
    dependency(request)
    try:
        dependency(request)
        assert False, "expected 429 via memory fallback"
    except Exception as exc:
        assert exc.status_code == 429
