"""PRD ТЗ№1 §33: warehouse movements (transfers between warehouses, logged corrections)."""

from app.models.enums import UserRole
from app.models.inventory import Inventory
from app.models.warehouse import Warehouse
from conftest import login, make_admin

API = "/api/v1/admin"


def _setup(client, db_session, sku, warehouse):
    other = Warehouse(name="Second", country="Uzbekistan")
    db_session.add(other)
    db_session.commit()
    make_admin(db_session, "wh@example.com", UserRole.WAREHOUSE_MANAGER)
    return other, login(client, "wh@example.com")


def _row(db_session, sku, warehouse):
    db_session.expire_all()
    return db_session.query(Inventory).filter_by(sku_id=sku.id, warehouse_id=warehouse.id).one_or_none()


def test_transfer_moves_stock_creates_the_target_row_and_is_logged(client, db_session, sku, warehouse):
    other, h = _setup(client, db_session, sku, warehouse)
    r = client.post(f"{API}/stock/transfer", json={"sku_code": sku.sku_code, "from_warehouse_id": warehouse.id, "to_warehouse_id": other.id, "quantity": 4, "note": "restock"}, headers=h)
    assert r.status_code == 201, r.text
    assert (_row(db_session, sku, warehouse).stock, _row(db_session, sku, other).stock) == (6, 4)  # total stays 10
    log = client.get(f"{API}/stock/movements?sku_id={sku.id}", headers=h).json()
    assert [(m["movement_type"], m["quantity"], m["note"]) for m in log] == [("transfer", 4, "restock")]

    from app.models.audit_log import AuditLog
    assert db_session.query(AuditLog).filter_by(action="stock_transfer").count() == 1


def test_cannot_move_reserved_or_missing_stock_or_to_the_same_place(client, db_session, sku, warehouse):
    other, h = _setup(client, db_session, sku, warehouse)
    inv = _row(db_session, sku, warehouse)
    inv.reserved = 8                      # 8 of the 10 are held by open orders
    db_session.commit()
    body = {"sku_id": sku.id, "from_warehouse_id": warehouse.id, "to_warehouse_id": other.id, "quantity": 3}
    r = client.post(f"{API}/stock/transfer", json=body, headers=h)
    assert r.status_code == 409 and "Only 2" in r.json()["detail"]
    assert _row(db_session, sku, warehouse).stock == 10 and _row(db_session, sku, other) is None  # nothing moved
    assert client.post(f"{API}/stock/transfer", json={**body, "to_warehouse_id": warehouse.id}, headers=h).status_code == 400
    assert client.post(f"{API}/stock/transfer", json={**body, "from_warehouse_id": other.id, "to_warehouse_id": warehouse.id}, headers=h).status_code == 409  # nothing there
    assert client.post(f"{API}/stock/transfer", json={**body, "quantity": 0}, headers=h).status_code == 422
    assert client.post(f"{API}/stock/transfer", json={"from_warehouse_id": 1, "to_warehouse_id": 2, "quantity": 1}, headers=h).status_code == 422
    assert client.post(f"{API}/stock/transfer", json={**body, "sku_id": 999}, headers=h).status_code == 404


def test_manual_correction_is_logged_with_its_delta(client, db_session, sku, warehouse):
    _other, h = _setup(client, db_session, sku, warehouse)
    assert client.patch(f"{API}/inventory/{sku.id}/{warehouse.id}", json={"stock": 7}, headers=h).status_code == 200
    log = client.get(f"{API}/stock/movements", headers=h).json()
    assert [(m["movement_type"], m["quantity"]) for m in log] == [("adjustment", -3)]


def test_only_warehouse_staff_can_transfer(client, db_session, sku, warehouse):
    make_admin(db_session, "sales@example.com", UserRole.SALES_MANAGER)
    r = client.post(f"{API}/stock/transfer", json={"sku_id": sku.id, "from_warehouse_id": 1, "to_warehouse_id": 2, "quantity": 1}, headers=login(client, "sales@example.com"))
    assert r.status_code == 403
    assert client.get(f"{API}/stock/movements").status_code == 401
