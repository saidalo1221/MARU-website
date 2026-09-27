"""Warehouse + per-warehouse inventory admin endpoints (PRD ТЗ№3 §27/§28)."""

from app.models.enums import UserRole
from conftest import login, make_admin


def test_sku_creation_requires_a_warehouse_first(client, db_session):
    from app.models.category import Category
    from app.models.product import Product
    from app.models.product_variant import ProductVariant

    category = Category(name="Containers", slug="containers")
    db_session.add(category)
    db_session.flush()
    product = Product(category_id=category.id, name="Food Container", slug="food-container", volume_ml=1000)
    db_session.add(product)
    db_session.flush()
    variant = ProductVariant(product_id=product.id, name="1000ml", color="clear")
    db_session.add(variant)
    db_session.commit()

    make_admin(db_session, "pm@example.com", UserRole.PRODUCT_MANAGER)
    make_admin(db_session, "wh@example.com", UserRole.WAREHOUSE_MANAGER)
    pm_headers = login(client, "pm@example.com")
    wh_headers = login(client, "wh@example.com")

    r = client.post(
        f"/api/v1/admin/variants/{variant.id}/skus", headers=pm_headers,
        json={"sku_code": "SKU-A", "retail_price": "9.99"},
    )
    assert r.status_code == 400
    assert "warehouse" in r.json()["detail"].lower()

    r = client.post(
        "/api/v1/admin/warehouses/", headers=wh_headers, json={"name": "Main", "country": "Uzbekistan", "priority": 1}
    )
    assert r.status_code == 201, r.text
    warehouse_id = r.json()["id"]

    r = client.post(
        f"/api/v1/admin/variants/{variant.id}/skus", headers=pm_headers,
        json={"sku_code": "SKU-A", "retail_price": "9.99"},
    )
    assert r.status_code == 201, r.text
    sku_id = r.json()["id"]

    r = client.get(f"/api/v1/admin/inventory/{sku_id}", headers=wh_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["warehouse_id"] == warehouse_id


def test_multiple_warehouses_per_sku(client, db_session, sku):
    make_admin(db_session, "wh2@example.com", UserRole.WAREHOUSE_MANAGER)
    headers = login(client, "wh2@example.com")

    r = client.post(
        "/api/v1/admin/warehouses/", headers=headers, json={"name": "Second", "country": "Uzbekistan", "priority": 2}
    )
    assert r.status_code == 201
    warehouse2_id = r.json()["id"]

    r = client.post(
        f"/api/v1/admin/inventory/{sku.id}", headers=headers, json={"warehouse_id": warehouse2_id, "stock": 50}
    )
    assert r.status_code == 201, r.text

    r = client.post(
        f"/api/v1/admin/inventory/{sku.id}", headers=headers, json={"warehouse_id": warehouse2_id, "stock": 5}
    )
    assert r.status_code == 409  # duplicate (sku, warehouse)

    r = client.get(f"/api/v1/admin/inventory/{sku.id}", headers=headers)
    assert len(r.json()) == 2

    r = client.patch(f"/api/v1/admin/inventory/{sku.id}/{warehouse2_id}", headers=headers, json={"stock": 100})
    assert r.status_code == 200 and r.json()["stock"] == 100


def test_public_catalog_reflects_aggregated_availability(client, sku):
    r = client.get("/api/v1/products/")
    assert r.status_code == 200
    variants = r.json()[0]["variants"]
    assert variants[0]["skus"][0]["available_quantity"] == 10
