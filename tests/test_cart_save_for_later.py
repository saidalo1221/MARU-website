"""Save for later (PRD ТЗ№2 §20): excluded from totals and checkout, survives
adding the same SKU, merge and checkout."""

from decimal import Decimal

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.inventory import Inventory
from conftest import CHECKOUT_PAYLOAD, register


def _add(client, sku, quantity, headers):
    r = client.post("/api/v1/cart/items", headers=headers, json={"sku_id": sku.id, "quantity": quantity})
    assert r.status_code == 201, r.text
    return r.json()


def test_saved_item_leaves_the_totals_and_item_count(client, sku):
    headers = register(client, "sfl1@example.com")
    _add(client, sku, 2, headers)
    cart = client.post(f"/api/v1/cart/items/{sku.id}/save-for-later", headers=headers).json()

    assert cart["items"] == [] and cart["item_count"] == 0
    assert Decimal(cart["subtotal"]) == 0 and Decimal(cart["total"]) == 0
    assert [(i["sku_id"], i["quantity"]) for i in cart["saved_items"]] == [(sku.id, 2)]
    assert Decimal(cart["saved_items"][0]["line_total"]) == Decimal("20.00")


def test_move_back_restores_it(client, sku):
    headers = register(client, "sfl2@example.com")
    _add(client, sku, 2, headers)
    client.post(f"/api/v1/cart/items/{sku.id}/save-for-later", headers=headers)
    cart = client.post(f"/api/v1/cart/items/{sku.id}/move-to-cart", headers=headers).json()
    assert cart["item_count"] == 2 and cart["saved_items"] == []
    assert Decimal(cart["subtotal"]) == Decimal("20.00")


def test_move_back_is_refused_when_stock_is_gone(client, sku, db_session):
    headers = register(client, "sfl3@example.com")
    _add(client, sku, 5, headers)
    client.post(f"/api/v1/cart/items/{sku.id}/save-for-later", headers=headers)
    db_session.query(Inventory).filter_by(sku_id=sku.id).one().stock = 2
    db_session.commit()
    r = client.post(f"/api/v1/cart/items/{sku.id}/move-to-cart", headers=headers)
    assert r.status_code == 400 and "INSUFFICIENT_STOCK" in r.json()["detail"]


def test_unknown_item_is_404(client, sku):
    headers = register(client, "sfl4@example.com")
    assert client.post(f"/api/v1/cart/items/{sku.id}/save-for-later", headers=headers).status_code == 404
    assert client.post(f"/api/v1/cart/items/{sku.id}/move-to-cart", headers=headers).status_code == 404


def test_adding_a_saved_sku_brings_it_back_to_the_cart(client, sku):
    headers = register(client, "sfl5@example.com")
    _add(client, sku, 2, headers)
    client.post(f"/api/v1/cart/items/{sku.id}/save-for-later", headers=headers)
    cart = _add(client, sku, 1, headers)
    assert cart["saved_items"] == []
    assert [(i["sku_id"], i["quantity"]) for i in cart["items"]] == [(sku.id, 3)]


def test_checkout_ignores_saved_items_and_keeps_them_for_next_time(client, sku, db_session):
    headers = register(client, "sfl6@example.com")
    _add(client, sku, 3, headers)
    client.post(f"/api/v1/cart/items/{sku.id}/save-for-later", headers=headers)
    # Checkout with only a saved item is an empty cart.
    assert client.post("/api/v1/orders/", headers=headers, json=CHECKOUT_PAYLOAD).status_code == 400

    _add(client, sku, 1, headers)  # brings the row back: 4 active
    client.post(f"/api/v1/cart/items/{sku.id}/save-for-later", headers=headers)
    assert client.post("/api/v1/orders/", headers=headers, json=CHECKOUT_PAYLOAD).status_code == 400


def test_saved_lines_survive_checkout_of_other_items(client, sku, db_session):
    from app.models.category import Category
    from app.models.product import Product
    from app.models.product_variant import ProductVariant
    from app.models.sku import SKU

    other_product = Product(category_id=db_session.query(Category).one().id, name="Lid", slug="lid", volume_ml=1000)
    db_session.add(other_product)
    db_session.flush()
    variant = ProductVariant(product_id=other_product.id, name="500ml", color="clear")
    db_session.add(variant)
    db_session.flush()
    other = SKU(variant_id=variant.id, sku_code="SKU-LID", retail_price=2, currency="USD")
    db_session.add(other)
    db_session.flush()
    warehouse_id = db_session.query(Inventory).one().warehouse_id
    db_session.add(Inventory(sku_id=other.id, warehouse_id=warehouse_id, stock=10, reserved=0))
    db_session.commit()

    headers = register(client, "sfl7@example.com")
    _add(client, sku, 1, headers)
    _add(client, other, 2, headers)
    client.post(f"/api/v1/cart/items/{other.id}/save-for-later", headers=headers)

    order = client.post("/api/v1/orders/", headers=headers, json=CHECKOUT_PAYLOAD)
    assert order.status_code == 201, order.text
    assert [i["sku_code_snapshot"] for i in order.json()["items"]] == ["SKU-1000-001"]

    cart = client.get("/api/v1/cart/", headers=headers).json()
    assert cart["items"] == []
    assert [(i["sku_code"], i["quantity"]) for i in cart["saved_items"]] == [("SKU-LID", 2)]


def test_guest_saved_item_is_merged_on_login(client, sku, db_session):
    first = client.post("/api/v1/cart/items", json={"sku_id": sku.id, "quantity": 2})
    token = first.headers["X-Cart-Token"]
    client.post(f"/api/v1/cart/items/{sku.id}/save-for-later", headers={"X-Cart-Token": token})

    headers = register(client, "sfl8@example.com")
    merged = client.post("/api/v1/cart/merge", headers={**headers, "X-Cart-Token": token}).json()
    assert merged["items"] == []
    assert [(i["sku_id"], i["quantity"]) for i in merged["saved_items"]] == [(sku.id, 2)]


def test_remove_deletes_a_saved_item(client, sku, db_session):
    headers = register(client, "sfl9@example.com")
    _add(client, sku, 1, headers)
    client.post(f"/api/v1/cart/items/{sku.id}/save-for-later", headers=headers)
    cart = client.delete(f"/api/v1/cart/items/{sku.id}", headers=headers).json()
    assert cart["saved_items"] == [] and db_session.query(CartItem).count() == 0
