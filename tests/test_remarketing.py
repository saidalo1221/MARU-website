"""Remarketing data for GA4 / Meta (product ids on events) and consent gating of everything sent to ad platforms."""

import pytest
import requests

from app.config import settings
from app.core.request_id import ads_consent_var
from app.models.enums import OrderStatus
from app.schemas.order import CheckoutRequest
from app.services.analytics import record_event
from app.services.integrations import ga4, meta
from app.services.order_service import create_order, set_order_status
from conftest import CHECKOUT_PAYLOAD
from test_orders_reservation import _cart_with

ITEMS = [{"item_id": "SKU-1", "item_name": "Container", "price": "10.00", "quantity": 2}, {"item_id": "SKU-2", "item_name": "Lid", "price": "1.50", "quantity": 1}]


def test_ga4_events_carry_ecommerce_items():
    p = ga4.build_payload("purchase", None, "s", {"order_id": 5, "value": "21.5", "currency": "USD", "items": ITEMS + [{"item_id": "X", "secret": "no"}]})
    items = p["events"][0]["params"]["items"]
    assert items[0] == {"item_id": "SKU-1", "item_name": "Container", "price": 10.0, "quantity": 2}
    assert items[2] == {"item_id": "X"}                                  # unknown keys are dropped
    assert p["events"][0]["params"]["transaction_id"] == 5


def test_meta_events_carry_content_ids_for_dynamic_ads():
    p = meta.build_payload("add_to_cart", None, "s", {"value": "21.5", "currency": "USD", "items": ITEMS})
    custom = p["data"][0]["custom_data"]
    assert custom["content_ids"] == ["SKU-1", "SKU-2"] and custom["content_type"] == "product" and custom["num_items"] == 3
    assert custom["contents"][0] == {"id": "SKU-1", "quantity": 2, "item_price": 10.0}


@pytest.fixture()
def platforms(monkeypatch):
    monkeypatch.setattr(settings, "GA4_MEASUREMENT_ID", "G-X")
    monkeypatch.setattr(settings, "GA4_API_SECRET", "s")
    monkeypatch.setattr(settings, "META_PIXEL_ID", "1")
    monkeypatch.setattr(settings, "META_CAPI_TOKEN", "t")
    sent = []
    monkeypatch.setattr(requests, "post", lambda url, **k: sent.append(url) or type("R", (), {"status_code": 200, "text": "{}", "raise_for_status": lambda self: None, "json": lambda self: {}})())
    return sent


def test_nothing_reaches_ad_platforms_without_consent(db_session, platforms):
    record_event(db_session, "add_to_cart", session_id="s", value="1", currency="USD")          # no consent header
    assert platforms == []
    token = ads_consent_var.set(True)
    try:
        record_event(db_session, "add_to_cart", session_id="s", value="1", currency="USD")
    finally:
        ads_consent_var.reset(token)
    assert len(platforms) == 2                                                                  # GA4 and Meta
    record_event(db_session, "add_to_cart", session_id="s", value="1", currency="USD", forward_ads=True)   # explicit (callbacks)
    assert len(platforms) == 4


def test_the_first_party_event_is_stored_whatever_the_consent(db_session, platforms):
    from app.models.analytics_event import AnalyticsEvent

    record_event(db_session, "add_to_cart", session_id="s")
    assert db_session.query(AnalyticsEvent).filter_by(event_name="add_to_cart").count() == 1


def test_purchase_is_forwarded_only_when_the_buyer_consented_at_checkout(client, db_session, sku, platforms):
    def place(consent):
        first = client.get("/api/v1/cart/")
        token = first.headers["X-Cart-Token"]
        client.post("/api/v1/cart/items", json={"sku_id": sku.id, "quantity": 1}, headers={"X-Cart-Token": token})
        headers = {"X-Cart-Token": token, **({"X-Ads-Consent": "1"} if consent else {})}
        r = client.post("/api/v1/orders/", json={**CHECKOUT_PAYLOAD, "payment_method": "payme"}, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()["id"]

    from app.models.order import Order

    yes, no = place(True), place(False)
    assert db_session.get(Order, yes).ads_consent is True and db_session.get(Order, no).ads_consent is False
    platforms.clear()
    set_order_status(db_session, db_session.get(Order, no), OrderStatus.PAID, None)      # paid later by a payment callback
    assert platforms == []
    set_order_status(db_session, db_session.get(Order, yes), OrderStatus.PAID, None)
    assert len(platforms) == 2 and any("google-analytics" in u for u in platforms) and any("facebook" in u for u in platforms)


def test_server_purchase_event_includes_the_items(db_session, sku, monkeypatch):
    seen = []
    monkeypatch.setattr(ga4, "forward", lambda name, uid, sid, props, db=None: seen.append((name, props)))
    monkeypatch.setattr(meta, "forward", lambda *a, **k: None)
    order = create_order(db_session, _cart_with(db_session, sku, 2), CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    order.ads_consent = True
    db_session.commit()
    set_order_status(db_session, order, OrderStatus.PAID, None)
    name, props = seen[0]
    assert name == "purchase" and props["items"] == [{"item_id": "SKU-1000-001", "item_name": "Food Container", "price": "10.00", "quantity": 2}]
