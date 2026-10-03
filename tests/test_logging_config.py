"""JSON log format, root-logger safety and optional Sentry startup."""

import json
import logging
import sys

from app.core import logging_config
from app.core.request_id import request_id_var


def _record(msg="hello %s", args=("world",), exc_info=None):
    record = logging.LogRecord("maru.test", logging.WARNING, __file__, 1, msg, args, exc_info)
    record.request_id = request_id_var.get()
    return record


def test_json_formatter_emits_one_parseable_line_with_request_id():
    token = request_id_var.set("req-json-1")
    try:
        line = logging_config.JsonFormatter().format(_record())
    finally:
        request_id_var.reset(token)
    data = json.loads(line)
    assert "\n" not in line
    assert (data["level"], data["logger"], data["request_id"], data["message"]) == ("WARNING", "maru.test", "req-json-1", "hello world")
    assert data["time"].endswith("+00:00")


def test_json_formatter_includes_exceptions_and_non_ascii():
    try:
        raise ValueError("boom")
    except ValueError:
        line = logging_config.JsonFormatter().format(_record("Заказ %s", ("№1",), sys.exc_info()))
    data = json.loads(line)
    assert "ValueError: boom" in data["exception"]
    assert data["message"] == "Заказ №1"


def test_configure_logging_leaves_an_existing_setup_alone(monkeypatch):
    root = logging.getLogger()
    before = list(root.handlers)
    assert before  # pytest's own capture handlers
    logging_config.configure_logging()
    assert root.handlers == before


def test_configure_logging_installs_json_handler_on_a_bare_root(monkeypatch):
    root = logging.getLogger()
    saved, level = root.handlers[:], root.level
    root.handlers = []
    monkeypatch.setattr(logging_config.settings, "LOG_FORMAT", "json")
    try:
        logging_config.configure_logging()
        assert isinstance(root.handlers[0].formatter, logging_config.JsonFormatter)
    finally:
        root.handlers = saved
        root.setLevel(level)


def test_sentry_is_off_without_a_dsn(monkeypatch):
    monkeypatch.setattr(logging_config.settings, "SENTRY_DSN", None)
    assert logging_config.init_error_tracking() is False


def test_missing_sentry_package_only_warns(monkeypatch, caplog):
    monkeypatch.setattr(logging_config.settings, "SENTRY_DSN", "https://key@example.ingest.sentry.io/1")
    monkeypatch.setitem(sys.modules, "sentry_sdk", None)  # makes `import sentry_sdk` raise ImportError
    assert logging_config.init_error_tracking() is False
    assert "sentry-sdk is not installed" in caplog.text


def test_sentry_init_is_called_without_personal_data(monkeypatch):
    calls = {}

    class _FakeSentry:
        @staticmethod
        def init(**kwargs):
            calls.update(kwargs)

    monkeypatch.setattr(logging_config.settings, "SENTRY_DSN", "https://key@example.ingest.sentry.io/1")
    monkeypatch.setitem(sys.modules, "sentry_sdk", _FakeSentry)
    assert logging_config.init_error_tracking() is True
    assert calls["send_default_pii"] is False and calls["dsn"].startswith("https://")
