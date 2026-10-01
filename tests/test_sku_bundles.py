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


def test_related_products_other_sizes_bought_together_and_sets(client, db_session, sku, warehouse):
    from app.models.product import Product
    from app.schemas.order import CheckoutRequest
    from app.services.order_service import create_order, set_order_status
    from app.models.enums import OrderStatus
    from conftest import CHECKOUT_PAYLOAD
    from test_orders_reservation import _cart_with
    from app.models.cart import Cart
    from app.models.cart_item import CartItem

    base = sku.variant.product                                    # 1000 ml, same category
    big = _extra_sku(db_session, warehouse, "BIG-1900", name="Big")
    big.variant.product.volume_ml = 1900
    other_shape = _extra_sku(db_session, warehouse, "OTHER-350", name="Other")
    other_shape.variant.product.shape = "square"
    base.shape = "round"
    big.variant.product.shape = "round"
    pack = _extra_sku(db_session, warehouse, "PACK-5", name="Pack")
    db_session.commit()

    make_admin(db_session, "pm@example.com", UserRole.PRODUCT_MANAGER)
    h = login(client, "pm@example.com")
    assert client.put(f"{API}/{pack.id}/bundle", json={"items": [{"sku_code": sku.sku_code, "quantity": 5}]}, headers=h).status_code == 200

    # a real order containing base + big makes "big" a co-purchase
    cart = Cart(token="rel-tok")
    db_session.add(cart)
    db_session.flush()
    db_session.add_all([CartItem(cart_id=cart.id, sku_id=sku.id, quantity=1), CartItem(cart_id=cart.id, sku_id=big.id, quantity=1)])
    db_session.commit()
    order = create_order(db_session, cart, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()
    set_order_status(db_session, order, OrderStatus.PAID, None)

    body = client.get(f"/api/v1/products/{base.slug}/related").json()
    assert [p["slug"] for p in body["other_sizes"]] == [big.variant.product.slug]      # same shape, other volume only
    assert [p["slug"] for p in body["bought_together"]] == [big.variant.product.slug]
    assert [p["slug"] for p in body["sets"]] == [pack.variant.product.slug]
    assert client.get("/api/v1/products/nope/related").status_code == 404
    assert Product
