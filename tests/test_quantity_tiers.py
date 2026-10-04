"""Quantity-break prices: admin editing, public exposure and the cart price (PRD ТЗ№2 §15)."""

from decimal import Decimal

from app.models.audit_log import AuditLog
from app.models.enums import UserRole
from app.models.exchange_rate import ExchangeRate
from conftest import login, make_admin


def _admin(client, db_session):
    make_admin(db_session, "pm@example.com", UserRole.PRODUCT_MANAGER)
    return login(client, "pm@example.com")


def test_admin_replaces_the_tier_set_and_it_is_public(client, db_session, sku):
    h = _admin(client, db_session)
    url = f"/api/v1/admin/skus/{sku.id}/tiers"

    r = client.put(url, json={"tiers": [{"min_quantity": 50, "price": "7.5"}, {"min_quantity": 10, "price": "9"}]}, headers=h)
    assert r.status_code == 200, r.text
    assert [(t["min_quantity"], Decimal(t["price"])) for t in r.json()["quantity_tiers"]] == [(10, Decimal("9")), (50, Decimal("7.5"))]

    public = client.get("/api/v1/products/food-container").json()
    tiers = public["variants"][0]["skus"][0]["quantity_tiers"]
    assert [t["min_quantity"] for t in tiers] == [10, 50]

    # Replacing drops the old rows; an empty list clears them.
    client.put(url, json={"tiers": [{"min_quantity": 20, "price": "8"}]}, headers=h)
    assert [t["min_quantity"] for t in client.get("/api/v1/products/food-container").json()["variants"][0]["skus"][0]["quantity_tiers"]] == [20]
    client.put(url, json={"tiers": []}, headers=h)
    assert client.get("/api/v1/products/food-container").json()["variants"][0]["skus"][0]["quantity_tiers"] == []

    audits = db_session.query(AuditLog).filter_by(action="sku_tiers_update").count()
    assert audits == 3


def test_tier_validation_and_permissions(client, db_session, sku):
    h = _admin(client, db_session)
    url = f"/api/v1/admin/skus/{sku.id}/tiers"
    assert client.put(url, json={"tiers": [{"min_quantity": 10, "price": "5"}, {"min_quantity": 10, "price": "4"}]}, headers=h).status_code == 422
    assert client.put(url, json={"tiers": [{"min_quantity": 1, "price": "5"}]}, headers=h).status_code == 422
    assert client.put(url, json={"tiers": [{"min_quantity": 5, "price": "0"}]}, headers=h).status_code == 422
    assert client.put("/api/v1/admin/skus/99999/tiers", json={"tiers": []}, headers=h).status_code == 404
    assert client.put(url, json={"tiers": []}).status_code in (401, 403)


def test_tier_prices_are_converted_to_the_display_currency(client, db_session, sku):
    h = _admin(client, db_session)
    db_session.add(ExchangeRate(currency="UZS", units_per_usd=Decimal("10000")))
    db_session.commit()
    client.put(f"/api/v1/admin/skus/{sku.id}/tiers", json={"tiers": [{"min_quantity": 10, "price": "9"}]}, headers=h)

    p = client.get("/api/v1/products/food-container", params={"currency": "UZS"}).json()
    s = p["variants"][0]["skus"][0]
    assert s["currency"] == "UZS" and Decimal(s["retail_price"]) == Decimal("100000")
    assert Decimal(s["quantity_tiers"][0]["price"]) == Decimal("90000")


def test_cart_price_follows_the_tier(client, db_session, sku):
    h = _admin(client, db_session)
    client.put(f"/api/v1/admin/skus/{sku.id}/tiers", json={"tiers": [{"min_quantity": 5, "price": "6"}]}, headers=h)
    first = client.post("/api/v1/cart/items", json={"sku_id": sku.id, "quantity": 1})
    assert Decimal(first.json()["items"][0]["unit_price"]) == Decimal("10.00")
    cart = {"X-Cart-Token": first.headers["X-Cart-Token"]}
    many = client.patch(f"/api/v1/cart/items/{sku.id}", json={"quantity": 5}, headers=cart).json()
    assert Decimal(many["items"][0]["unit_price"]) == Decimal("6.00")
