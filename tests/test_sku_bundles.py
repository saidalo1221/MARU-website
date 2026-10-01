"""PRD ТЗ№1 §7: set / pack SKUs describe what is inside them."""

from app.models.category import Category
from app.models.enums import UserRole
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.sku import SKU
from conftest import login, make_admin

API = "/api/v1/admin/skus"


def _extra_sku(db_session, warehouse, code, color="white", name="Lid"):
    category = db_session.query(Category).first()
    product = Product(category_id=category.id, name=name, slug=f"{name.lower()}-{code.lower()}", volume_ml=350)
    db_session.add(product)
    db_session.flush()
    variant = ProductVariant(product_id=product.id, name=f"{name} {color}", color=color)
    db_session.add(variant)
    db_session.flush()
    sku = SKU(variant_id=variant.id, sku_code=code, retail_price=2, currency="USD")
    db_session.add(sku)
    db_session.flush()
    db_session.add(Inventory(sku_id=sku.id, warehouse_id=warehouse.id, stock=50, reserved=0))
    db_session.commit()
    return sku


def test_set_contents_are_saved_shown_publicly_and_replaced(client, db_session, sku, warehouse):
    lid = _extra_sku(db_session, warehouse, "LID-W")
    make_admin(db_session, "pm@example.com", UserRole.PRODUCT_MANAGER)
    h = login(client, "pm@example.com")
    r = client.put(f"{API}/{sku.id}/bundle", json={"items": [{"sku_code": "LID-W", "quantity": 5}, {"sku_code": "LID-W", "quantity": 2}]}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["bundle_items"] == [{"sku_code": "LID-W", "product_name": "Lid", "variant_name": "Lid white", "color": "white", "quantity": 7}]  # same SKU twice adds up

    page = client.get(f"/api/v1/products/{sku.variant.product.slug}").json()
    assert page["variants"][0]["skus"][0]["bundle_items"][0]["quantity"] == 7
    assert client.put(f"{API}/{sku.id}/bundle", json={"items": []}, headers=h).json()["bundle_items"] == []
    assert lid.id


def test_validation_no_self_unknown_or_nested_sets(client, db_session, sku, warehouse):
    other = _extra_sku(db_session, warehouse, "PACK-3")
    _extra_sku(db_session, warehouse, "LID-W")
    make_admin(db_session, "pm@example.com", UserRole.PRODUCT_MANAGER)
    h = login(client, "pm@example.com")
    assert client.put(f"{API}/{sku.id}/bundle", json={"items": [{"sku_code": sku.sku_code, "quantity": 1}]}, headers=h).status_code == 400
    assert client.put(f"{API}/{sku.id}/bundle", json={"items": [{"sku_code": "NOPE", "quantity": 1}]}, headers=h).status_code == 404
    assert client.put(f"{API}/{sku.id}/bundle", json={"items": [{"sku_code": "LID-W", "quantity": 0}]}, headers=h).status_code == 422
    assert client.put(f"{API}/{other.id}/bundle", json={"items": [{"sku_code": "LID-W", "quantity": 2}]}, headers=h).status_code == 200
    r = client.put(f"{API}/{sku.id}/bundle", json={"items": [{"sku_code": "PACK-3", "quantity": 1}]}, headers=h)  # PACK-3 is now a set
    assert r.status_code == 400 and "nested" in r.json()["detail"]
    assert client.put(f"{API}/{sku.id}/bundle", json={"items": [{"sku_code": "LID-W", "quantity": 1}]}).status_code == 401
