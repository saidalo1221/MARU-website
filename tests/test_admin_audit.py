"""PRD ТЗ№3 §81: price changes, stock changes and admin actions leave audit rows."""

import json

from app.models.audit_log import AuditLog
from app.models.enums import UserRole
from conftest import login, make_admin, register

BASE = "/api/v1/admin"


def _admin(client, db_session):
    make_admin(db_session, "root@example.com", UserRole.SUPER_ADMIN)
    return login(client, "root@example.com")


def _rows(db_session, action):
    db_session.expire_all()
    return db_session.query(AuditLog).filter_by(action=action).order_by(AuditLog.id).all()


def test_pricing_rules_are_audited(client, db_session):
    h = _admin(client, db_session)

    r = client.post(f"{BASE}/exchange-rates/", json={"currency": "EUR", "units_per_usd": "0.9"}, headers=h)
    assert r.status_code == 201, r.text
    rid = r.json()["id"]
    assert client.patch(f"{BASE}/exchange-rates/{rid}", json={"units_per_usd": "0.95"}, headers=h).status_code == 200
    (update,) = _rows(db_session, "exchange_rate_update")
    assert json.loads(update.old_value)["units_per_usd"] in ("0.900000", "0.9")
    assert "0.95" in update.new_value
    assert client.delete(f"{BASE}/exchange-rates/{rid}", headers=h).status_code == 204
    assert len(_rows(db_session, "exchange_rate_create")) == 1
    assert len(_rows(db_session, "exchange_rate_delete")) == 1

    p = client.post(f"{BASE}/promo-codes/", json={"code": "AUD1", "discount_type": "percent", "discount_value": "10"}, headers=h)
    assert p.status_code == 201, p.text
    client.patch(f"{BASE}/promo-codes/{p.json()['id']}", json={"discount_value": "20"}, headers=h)
    assert len(_rows(db_session, "promo_create")) == 1
    assert json.loads(_rows(db_session, "promo_update")[0].new_value) == {"discount_value": "20"}

    s = client.post(f"{BASE}/shipping-rates/", json={"country": "Peru", "delivery_method": "courier"}, headers=h)
    assert s.status_code == 201, s.text
    client.patch(f"{BASE}/shipping-rates/{s.json()['id']}", json={"base_fee": "7"}, headers=h)
    assert len(_rows(db_session, "shipping_rate_create")) == 1
    assert len(_rows(db_session, "shipping_rate_update")) == 1

    t = client.post(f"{BASE}/tax-rules/", json={"country": "Peru", "customer_type": "*", "rate": "18"}, headers=h)
    assert t.status_code == 201, t.text
    client.patch(f"{BASE}/tax-rules/{t.json()['id']}", json={"rate": "19"}, headers=h)
    assert len(_rows(db_session, "tax_rule_create")) == 1
    assert len(_rows(db_session, "tax_rule_update")) == 1


def test_stock_sku_product_and_warehouse_changes_are_audited(client, db_session, sku):
    h = _admin(client, db_session)

    w = client.post(f"{BASE}/warehouses/", json={"name": "Second", "country": "Uzbekistan"}, headers=h)
    assert w.status_code == 201, w.text
    client.patch(f"{BASE}/warehouses/{w.json()['id']}", json={"priority": 5}, headers=h)
    assert len(_rows(db_session, "warehouse_create")) == 1
    assert len(_rows(db_session, "warehouse_update")) == 1

    inv = client.post(f"{BASE}/inventory/{sku.id}", json={"warehouse_id": w.json()["id"], "stock": 4}, headers=h)
    assert inv.status_code == 201, inv.text
    (created,) = _rows(db_session, "inventory_create")
    assert json.loads(created.new_value)["stock"] == 4

    new_sku = client.post(
        f"{BASE}/variants/{sku.variant_id}/skus", json={"sku_code": "AUD-1", "retail_price": "3.5", "currency": "USD"}, headers=h
    )
    assert new_sku.status_code == 201, new_sku.text
    assert len(_rows(db_session, "sku_create")) == 1

    pid = sku.variant.product_id
    assert client.patch(f"{BASE}/products/{pid}", json={"min_order_quantity": 2}, headers=h).status_code == 200
    (pu,) = _rows(db_session, "product_update")
    assert json.loads(pu.old_value) == {"min_order_quantity": 1}


def test_role_changes_are_audited(client, db_session):
    h = _admin(client, db_session)
    register(client, "staff@example.com")

    r = client.post(f"{BASE}/users/promote", json={"email": "staff@example.com", "role": "accountant"}, headers=h)
    assert r.status_code == 200, r.text
    client.post(f"{BASE}/users/{r.json()['id']}/demote", headers=h)
    rows = _rows(db_session, "admin_role_change")
    assert len(rows) == 2
    assert json.loads(rows[0].old_value) == {"role": "customer"}
    assert json.loads(rows[0].new_value) == {"role": "accountant"}
    assert json.loads(rows[1].new_value) == {"role": "customer"}


def test_audit_rows_record_the_request_id_and_client_ip(client, db_session):
    h = _admin(client, db_session)
    r = client.post(
        f"{BASE}/exchange-rates/", json={"currency": "EUR", "units_per_usd": "0.9"},
        headers={**h, "X-Request-ID": "audit-req-0001"},
    )
    assert r.status_code == 201, r.text
    (row,) = _rows(db_session, "exchange_rate_create")
    assert row.request_id == "audit-req-0001"
    assert row.ip_address == "testclient"  # Starlette's TestClient host
