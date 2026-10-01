"""The business decides where products are sold and what they cost, in the admin panel."""

from decimal import Decimal

from app.models.enums import UserRole
from app.models.product import Product
from app.models.sku import SKU
from conftest import login, make_admin
from test_catalog_search import _catalog, _slugs


def _pm(client, db_session, role=UserRole.PRODUCT_MANAGER, email="pm@example.com"):
    make_admin(db_session, email, role)
    return login(client, email)


def test_markets_screen_lists_filters_and_bulk_sets_countries(client, db_session, warehouse):
    cats, round_, square, bento = _catalog(db_session, warehouse)
    h = _pm(client, db_session)
    rows = client.get("/api/v1/admin/markets/", headers=h).json()
    assert {r["slug"] for r in rows} == {"round", "square", "bento"} and all(r["sold_in_countries"] is None for r in rows)
    assert [r["slug"] for r in client.get("/api/v1/admin/markets/?q=BENTO", headers=h).json()] == ["bento"]
    assert {r["slug"] for r in client.get(f"/api/v1/admin/markets/?category_id={cats['food-containers'].id}", headers=h).json()} == {"round", "square"}

    r = client.put("/api/v1/admin/markets/bulk", json={"product_ids": [round_.id, square.id], "set_sold": True, "sold_in_countries": ["uzbekistan", "Uzbekistan", " Kazakhstan "]}, headers=h)
    assert r.status_code == 200 and r.json() == {"updated": 2}
    db_session.expire_all()
    assert db_session.get(Product, round_.id).sold_in_countries == ["Kazakhstan", "uzbekistan"]    # trimmed, de-duplicated
    assert [x["slug"] for x in client.get("/api/v1/admin/markets/?restricted_only=true", headers=h).json()] == ["square", "round"]
    assert "round" not in _slugs(client.get("/api/v1/products/", params={"country": "Germany"}))     # takes effect at once (cache cleared)

    client.put("/api/v1/admin/markets/bulk", json={"product_ids": [square.id], "set_hidden": True, "hidden_in_countries": ["Germany"]}, headers=h)
    db_session.expire_all()
    assert db_session.get(Product, square.id).sold_in_countries == ["Kazakhstan", "uzbekistan"] and db_session.get(Product, square.id).hidden_in_countries == ["Germany"]  # the other list was left alone
    client.put("/api/v1/admin/markets/bulk", json={"product_ids": [round_.id, square.id], "set_sold": True, "set_hidden": True}, headers=h)   # "sell everywhere"
    db_session.expire_all()
    assert all(db_session.get(Product, i).sold_in_countries is None and db_session.get(Product, i).hidden_in_countries is None for i in (round_.id, square.id))
    assert client.put("/api/v1/admin/markets/bulk", json={"product_ids": [round_.id]}, headers=h).status_code == 400
    assert client.put("/api/v1/admin/markets/bulk", json={"product_ids": [9999], "set_sold": True}, headers=h).status_code == 404


def test_only_product_managers_use_markets_and_costs(client, db_session, sku):
    sales = _pm(client, db_session, UserRole.SALES_MANAGER, "s@example.com")
    assert client.get("/api/v1/admin/markets/", headers=sales).status_code == 403
    assert client.get("/api/v1/admin/costs/", headers=sales).status_code == 403
    assert client.get("/api/v1/admin/costs/").status_code == 401
    acct = _pm(client, db_session, UserRole.ACCOUNTANT, "a@example.com")
    assert client.get("/api/v1/admin/costs/", headers=acct).status_code == 200


def test_costs_screen_lists_margin_and_imports_many_at_once(client, db_session, sku):
    h = _pm(client, db_session)
    rows = client.get("/api/v1/admin/costs/", headers=h).json()
    assert rows[0]["sku_code"] == "SKU-1000-001" and rows[0]["cost_price"] is None and rows[0]["margin_percent"] is None
    assert len(client.get("/api/v1/admin/costs/?missing_only=true", headers=h).json()) == 1

    r = client.put("/api/v1/admin/costs/bulk", json={"items": [{"sku_code": "SKU-1000-001", "cost_price": "6.5"}, {"sku_code": "NOPE-1", "cost_price": "1"}]}, headers=h)
    assert r.json() == {"updated": 1, "unknown": ["NOPE-1"]}
    row = client.get("/api/v1/admin/costs/?q=1000", headers=h).json()[0]
    assert Decimal(row["cost_price"]) == Decimal("6.50") and row["margin_percent"] == 35.0
    assert client.get("/api/v1/admin/costs/?missing_only=true", headers=h).json() == []
    assert client.put("/api/v1/admin/costs/bulk", json={"items": [{"sku_code": "SKU-1000-001", "cost_price": "6.50"}]}, headers=h).json()["updated"] == 0   # unchanged
    assert client.put("/api/v1/admin/costs/bulk", json={"items": [{"sku_code": "SKU-1000-001", "cost_price": None}]}, headers=h).json()["updated"] == 1  # cleared
    assert client.put("/api/v1/admin/costs/bulk", json={"items": [{"sku_code": "SKU-1000-001", "cost_price": "-1"}]}, headers=h).status_code == 422
    assert db_session.query(SKU).one().cost_price is None
    from app.models.audit_log import AuditLog
    assert db_session.query(AuditLog).filter_by(action="sku_cost_bulk_update").count() == 3
