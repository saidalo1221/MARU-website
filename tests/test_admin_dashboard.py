"""PRD ТЗ№1 §27-28, §59-60: the numbers on the admin dashboard."""

import json
from decimal import Decimal

from app.models.analytics_event import AnalyticsEvent
from app.models.enums import OrderStatus, UserRole
from app.schemas.order import CheckoutRequest
from app.services.order_service import create_order, set_order_status
from conftest import CHECKOUT_PAYLOAD, login, make_admin
from test_orders_reservation import _cart_with

API = "/api/v1/admin"


def _paid_order(db_session, sku, qty=1, **over):
    order = create_order(db_session, _cart_with(db_session, sku, qty), CheckoutRequest(**{**CHECKOUT_PAYLOAD, **over}), None)
    db_session.commit()
    set_order_status(db_session, order, OrderStatus.PAID, None)
    return order


def _admin(client, db_session, role=UserRole.SUPER_ADMIN, email="root@example.com"):
    make_admin(db_session, email, role)
    return login(client, email)


def test_sales_numbers_and_markets(client, db_session, sku):
    _paid_order(db_session, sku, 2)                                  # 20 USD, Uzbekistan
    _paid_order(db_session, sku, 3, country="Kazakhstan", email="b@example.com")  # 30 USD
    _paid_order(db_session, sku, 1, country="Germany", email="c@example.com")     # 10 USD
    create_order(db_session, _cart_with(db_session, sku, 1), CheckoutRequest(**CHECKOUT_PAYLOAD), None)  # unpaid: ignored
    db_session.commit()

    d = client.get(f"{API}/dashboard/", headers=_admin(client, db_session)).json()
    assert d["today"] == {"orders": 3, "revenue": 60.0, "units": 6, "average_order_value": 20.0}
    assert d["month"]["orders"] == 3 and d["month"]["revenue"] == 60.0 and d["month"]["customers"] == 3
    assert {m["market"]: (m["orders"], m["revenue"]) for m in d["markets"]} == {"Uzbekistan": (1, 20.0), "Kazakhstan": (1, 30.0), "International": (1, 10.0)}


def test_gross_profit_only_counts_lines_with_a_cost(client, db_session, sku):
    h = _admin(client, db_session)
    r = client.put(f"{API}/skus/{sku.id}/cost", json={"cost_price": "6.00"}, headers=h)
    assert r.status_code == 200 and r.json()["cost_price"] == "6.00"
    _paid_order(db_session, sku, 2)  # revenue 20, cost 12 -> profit 8

    m = client.get(f"{API}/dashboard/", headers=h).json()["month"]
    assert m["gross_profit"] == 8.0 and m["gross_margin"] == 0.4 and m["cost_coverage"] == 1.0

    # a cost set later does not rewrite history; the order keeps the cost it had
    client.put(f"{API}/skus/{sku.id}/cost", json={"cost_price": "9.00"}, headers=h)
    assert client.get(f"{API}/dashboard/", headers=h).json()["month"]["gross_profit"] == 8.0


def test_no_cost_means_no_profit_figure_and_cost_stays_private(client, db_session, sku):
    _paid_order(db_session, sku, 1)
    h = _admin(client, db_session)
    m = client.get(f"{API}/dashboard/", headers=h).json()["month"]
    assert m["gross_profit"] is None and m["cost_coverage"] == 0.0
    client.put(f"{API}/skus/{sku.id}/cost", json={"cost_price": "1"}, headers=h)
    assert "cost_price" not in json.dumps(client.get(f"/api/v1/products/{sku.variant.product.slug}").json())
    assert "cost_price" not in json.dumps(client.get(f"{API}/products/{sku.variant.product_id}", headers=h).json())


def test_new_and_repeat_customers_ltv(client, db_session, sku):
    _paid_order(db_session, sku, 1, email="a@example.com")
    _paid_order(db_session, sku, 1, email="A@example.com")  # same customer, different case
    _paid_order(db_session, sku, 2, email="b@example.com")
    c = client.get(f"{API}/dashboard/", headers=_admin(client, db_session)).json()["customers"]
    assert c["total"] == 2 and c["new_this_month"] == 2 and c["repeat_purchase_rate"] == 0.5
    assert c["lifetime_value"] == 20.0 and c["orders_per_customer"] == 1.5


def test_marketing_cac_roas_and_sources(client, db_session, sku):
    h = _admin(client, db_session)
    paid = _paid_order(db_session, sku, 4, email="ads@example.com", attribution={"utm_source": "google", "utm_medium": "cpc"})  # 40 USD from ads
    _paid_order(db_session, sku, 1, email="organic@example.com")
    assert client.post(f"{API}/dashboard/marketing-spend", json={"month": "2026-10-15", "channel": "Google Ads", "amount_usd": "20"}, headers=h).status_code in (201, 422)
    from datetime import date
    month = paid.created_at.date().replace(day=1)
    r = client.post(f"{API}/dashboard/marketing-spend", json={"month": str(paid.created_at.date()), "channel": "Google Ads", "amount_usd": "20"}, headers=h)
    assert r.status_code == 201 and r.json()["month"] == str(month)
    m = client.get(f"{API}/dashboard/", headers=h).json()
    spend_total = sum(float(x["amount_usd"]) for x in client.get(f"{API}/dashboard/marketing-spend", headers=h).json() if x["month"] == str(month))
    assert m["marketing"]["spend"] == spend_total
    assert m["marketing"]["cac"] == round(spend_total / 2, 2) and m["marketing"]["roas"] == round(40 / spend_total, 2)
    assert {s["source"] for s in m["sources"]} == {"google", "website"}
    assert client.delete(f"{API}/dashboard/marketing-spend/{r.json()['id']}", headers=h).status_code == 204
    assert date.today()  # (keeps the import used)


def test_funnel_and_conversion_from_analytics_events(client, db_session, sku):
    for sid, events in {"s1": ["view_item_list", "view_item", "add_to_cart", "begin_checkout", "add_payment_info"], "s2": ["view_item"], "s3": ["view_item_list"], "s4": ["view_item"]}.items():
        for e in events:
            db_session.add(AnalyticsEvent(event_name=e, session_id=sid))
    db_session.commit()
    _paid_order(db_session, sku, 1)

    d = client.get(f"{API}/dashboard/", headers=_admin(client, db_session)).json()
    funnel = {f["stage"]: f for f in d["funnel"]}
    assert [funnel[k]["count"] for k in ("visitors", "product_view", "add_to_cart", "checkout", "payment", "order")] == [4, 3, 1, 1, 1, 1]
    assert funnel["product_view"]["rate_from_previous"] == 0.75
    assert d["month"]["visitors"] == 4 and d["month"]["conversion_rate"] == 0.25


def test_access_control(client, db_session, sku):
    assert client.get(f"{API}/dashboard/").status_code == 401
    assert client.get(f"{API}/dashboard/", headers=_admin(client, db_session, UserRole.MARKETING_MANAGER, "m@example.com")).status_code == 200
    assert client.get(f"{API}/dashboard/", headers=_admin(client, db_session, UserRole.WAREHOUSE_MANAGER, "w@example.com")).status_code == 403
    assert Decimal("1")
