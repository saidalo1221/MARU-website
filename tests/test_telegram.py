"""Telegram connector: formats the request, never leaks the token, quiet when unconfigured."""

import logging

import requests

from app.config import settings
from app.services.integrations import adapters, telegram


class _Resp:
    def __init__(self, status=200, body=None):
        self.status_code, self._body, self.text = status, body or {"ok": True}, str(body)

    def json(self):
        return self._body


def test_unconfigured_is_the_null_adapter(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "")
    adapters._REGISTERED.pop("telegram", None)
    assert adapters.get_adapter("telegram").send("1", "x") is False
    assert telegram.notify_admin("x") is False


def test_send_posts_to_the_bot_api(monkeypatch):
    calls = []
    monkeypatch.setattr(requests, "post", lambda url, json=None, timeout=None: calls.append((url, json)) or _Resp())
    assert telegram.TelegramAdapter("123:abc").send("42", "hello") is True
    assert calls == [("https://api.telegram.org/bot123:abc/sendMessage", {"chat_id": "42", "text": "hello", "disable_web_page_preview": True})]


def test_registry_builds_it_from_settings_and_admin_alert_uses_the_admin_chat(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setattr(settings, "TELEGRAM_ADMIN_CHAT_ID", "-100777")
    adapters._REGISTERED.pop("telegram", None)
    assert isinstance(adapters.get_adapter("telegram"), telegram.TelegramAdapter)
    sent = []
    monkeypatch.setattr(requests, "post", lambda url, json=None, timeout=None: sent.append(json["chat_id"]) or _Resp())
    assert telegram.notify_admin("alert") is True and sent == ["-100777"]
    adapters._REGISTERED.pop("telegram", None)


def test_failures_return_false_and_do_not_log_the_token(monkeypatch, caplog):
    def boom(url, json=None, timeout=None):
        raise requests.ConnectionError(f"failed for {url}")

    monkeypatch.setattr(requests, "post", boom)
    with caplog.at_level(logging.DEBUG):
        assert telegram.TelegramAdapter("123:SECRET").send("1", "x") is False
    assert "SECRET" not in caplog.text
    monkeypatch.setattr(requests, "post", lambda *a, **k: _Resp(403, {"ok": False}))
    assert telegram.TelegramAdapter("t").send("1", "x") is False
