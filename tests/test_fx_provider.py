"""Live FX rate sync (PRD ТЗ№3 §14). Mocks the HTTP call — never hits the
real exchangerate-api.com from the test suite; that would burn the free
tier's 1,500 requests/month on every test run."""

from decimal import Decimal

import pytest

from app.models.enums import UserRole
from app.models.exchange_rate import ExchangeRate
from app.services.fx_provider import FxProviderError, fetch_all_rates, fetch_rate_for_currency, sync_exchange_rates
from conftest import login, make_admin


class _FakeResponse:
    def __init__(self, json_body, status_code=200):
        self._json = json_body
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._json


_SUCCESS_BODY = {
    "result": "success",
    "conversion_rates": {"USD": 1, "UZS": 12500, "EUR": "0.92", "KZT": 450, "AED": "3.67", "RUB": 90},
}


def test_fetch_all_rates_requires_api_key(monkeypatch):
    import app.config as config_module

    monkeypatch.setattr(config_module.settings, "EXCHANGERATE_API_KEY", None)
    with pytest.raises(FxProviderError, match="not configured"):
        fetch_all_rates()


def test_fetch_all_rates_returns_every_currency_but_usd(monkeypatch):
    import app.config as config_module
    import app.services.fx_provider as fx_module

    monkeypatch.setattr(config_module.settings, "EXCHANGERATE_API_KEY", "test-key")
    monkeypatch.setattr(fx_module.requests, "get", lambda url, timeout: _FakeResponse(_SUCCESS_BODY))

    rates = fetch_all_rates()
    assert rates == {
        "UZS": Decimal("12500"),
        "EUR": Decimal("0.92"),
        "KZT": Decimal("450"),
        "AED": Decimal("3.67"),
        "RUB": Decimal("90"),
    }
    assert "USD" not in rates  # implicit base, never stored


def test_fetch_all_rates_raises_on_provider_error(monkeypatch):
    import app.config as config_module
    import app.services.fx_provider as fx_module

    monkeypatch.setattr(config_module.settings, "EXCHANGERATE_API_KEY", "test-key")
    monkeypatch.setattr(
        fx_module.requests, "get", lambda url, timeout: _FakeResponse({"result": "error", "error-type": "invalid-key"})
    )
    with pytest.raises(FxProviderError, match="invalid-key"):
        fetch_all_rates()


def test_fetch_rate_for_currency_raises_when_provider_lacks_it(monkeypatch):
    import app.config as config_module
    import app.services.fx_provider as fx_module

    monkeypatch.setattr(config_module.settings, "EXCHANGERATE_API_KEY", "test-key")
    incomplete = {"result": "success", "conversion_rates": {"USD": 1, "UZS": 12500}}
    monkeypatch.setattr(fx_module.requests, "get", lambda url, timeout: _FakeResponse(incomplete))
    with pytest.raises(FxProviderError, match="no rate for EUR"):
        fetch_rate_for_currency("EUR")


def test_sync_exchange_rates_creates_and_updates(db_session, monkeypatch):
    import app.config as config_module
    import app.services.fx_provider as fx_module

    monkeypatch.setattr(config_module.settings, "EXCHANGERATE_API_KEY", "test-key")
    monkeypatch.setattr(fx_module.requests, "get", lambda url, timeout: _FakeResponse(_SUCCESS_BODY))

    # Pre-existing stale row for one currency — must be updated, not duplicated.
    db_session.add(ExchangeRate(currency="UZS", units_per_usd=Decimal("11000")))
    db_session.commit()

    # Only currencies already in the table are refreshed once it is non-empty.
    updated_count = sync_exchange_rates(db_session)
    assert updated_count == 1

    rows = {r.currency: r.units_per_usd for r in db_session.query(ExchangeRate).all()}
    assert rows == {"UZS": Decimal("12500")}  # updated in place, no duplicate row


def test_sync_exchange_rates_bootstraps_defaults_on_empty_table(db_session, monkeypatch):
    import app.config as config_module
    import app.services.fx_provider as fx_module

    monkeypatch.setattr(config_module.settings, "EXCHANGERATE_API_KEY", "test-key")
    monkeypatch.setattr(fx_module.requests, "get", lambda url, timeout: _FakeResponse(_SUCCESS_BODY))

    assert sync_exchange_rates(db_session) == 4
    rows = {r.currency: r.units_per_usd for r in db_session.query(ExchangeRate).all()}
    assert rows["EUR"] == Decimal("0.92")
    assert set(rows) == {"UZS", "EUR", "KZT", "AED"}  # RUB is not a default


def test_admin_sync_endpoint(client, db_session, monkeypatch):
    import app.config as config_module
    import app.services.fx_provider as fx_module

    monkeypatch.setattr(config_module.settings, "EXCHANGERATE_API_KEY", "test-key")
    monkeypatch.setattr(fx_module.requests, "get", lambda url, timeout: _FakeResponse(_SUCCESS_BODY))

    make_admin(db_session, "pm@example.com", UserRole.PRODUCT_MANAGER)
    headers = login(client, "pm@example.com")

    r = client.post("/api/v1/admin/exchange-rates/sync", headers=headers)
    assert r.status_code == 200, r.text
    currencies = {row["currency"] for row in r.json()}
    assert currencies == {"UZS", "EUR", "KZT", "AED"}


def test_admin_sync_endpoint_surfaces_provider_failure(client, db_session, monkeypatch):
    import app.config as config_module

    monkeypatch.setattr(config_module.settings, "EXCHANGERATE_API_KEY", None)

    make_admin(db_session, "pm2@example.com", UserRole.PRODUCT_MANAGER)
    headers = login(client, "pm2@example.com")

    r = client.post("/api/v1/admin/exchange-rates/sync", headers=headers)
    assert r.status_code == 502
