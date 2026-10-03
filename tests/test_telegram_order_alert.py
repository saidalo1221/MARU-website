from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from app.services.integrations import telegram


def _order(**over):
    item = SimpleNamespace(product_name_snapshot="MARU Lunch Box", variant_name_snapshot="Blue", sku_code_snapshot="LBX-800",
                           quantity=3, unit_price=Decimal("4.20"))
    base = dict(order_number="MARU-20261003-ABC123", id=7, first_name="Ali", last_name="Valiyev", company_name=None,
                phone="+998901112233", email="ali@example.com", items=[item], currency="USD",
                subtotal_amount=Decimal("12.60"), discount_amount=Decimal("0"), tax_amount=Decimal("0"),
                delivery_amount=Decimal("2.00"), total_amount=Decimal("14.60"), payment_method="payme",
                payment_status="created", delivery_method="courier", address_line="Amir Temur 1", city="Tashkent",
                region=None, postal_code="100000", country="UZ", notes="Call before arriving", created_at=datetime(2026, 10, 3))
    base.update(over)
    return SimpleNamespace(**base)


def test_alert_has_customer_items_totals_location_and_admin_link(monkeypatch):
    monkeypatch.setattr(telegram.settings, "FRONTEND_URL", "https://maru.example")
    text = telegram.build_order_alert(_order(), "en")
    for part in ("MARU-20261003-ABC123", "Ali Valiyev", "+998901112233", "MARU Lunch Box (Blue) [LBX-800] x3 @ 4.20 USD",
                 "TOTAL: 14.60 USD", "Address: Amir Temur 1, Tashkent, 100000, UZ", "query=Amir%20Temur%201%2C%20Tashkent%2C%20UZ",
                 "Note: Call before arriving", "https://maru.example/admin/orders/7"):
        assert part in text, part
    assert "Discount" not in text


def test_alert_is_skipped_without_bot_settings(monkeypatch):
    monkeypatch.setattr(telegram.settings, "TELEGRAM_BOT_TOKEN", "")
    sent = []
    monkeypatch.setattr(telegram, "notify_admin", lambda text: sent.append(text))
    telegram.notify_new_order(_order())
    assert sent == []


def test_alert_is_translated_and_language_is_configurable(monkeypatch):
    ru = telegram.build_order_alert(_order(), "ru")
    assert "Новый заказ MARU-20261003-ABC123" in ru and "ИТОГО: 14.60 USD" in ru and "оплата" not in ru.lower() or "Оплата: payme (создана)" in ru
    uz = telegram.build_order_alert(_order(), "uz")
    assert "Yangi buyurtma" in uz and "JAMI: 14.60 USD" in uz and "(yaratildi)" in uz
    # default comes from the setting; "order" follows the customer's language; unknown codes fall back to English
    monkeypatch.setattr(telegram.settings, "TELEGRAM_ALERT_LANG", "uz")
    assert "Yangi buyurtma" in telegram.build_order_alert(_order())
    monkeypatch.setattr(telegram.settings, "TELEGRAM_ALERT_LANG", "order")
    assert "Новый заказ" in telegram.build_order_alert(_order(language="ru"))
    assert "New order" in telegram.build_order_alert(_order(), "de")
