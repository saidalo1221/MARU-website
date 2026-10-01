"""PRD ТЗ№3 §74 (product-level tax) and §23 (promo targeting + per-customer limits)."""

import uuid
from decimal import Decimal

import pytest

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.category import Category
from app.models.enums import OrderStatus
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.promo_code import PromoCode, PromoDiscountType
from app.models.sku import SKU
from app.models.tax_rule import TaxRule
from app.schemas.order import CheckoutRequest
from app.services.order_service import OrderError, create_order, set_order_status
from conftest import CHECKOUT_PAYLOAD


def _add_product(db_session, warehouse, slug, price, tax_class="standard", category=None):
    category = category or db_session.query(Category).first()
    if category is None:
        category = Category(name="Containers", slug="containers")
        db_session.add(category)
        db_session.flush()
    product = Product(category_id=category.id, name=slug, slug=slug, volume_ml=1000, tax_class=tax_class)
    db_session.add(product)
    db_session.flush()
    variant = ProductVariant(product_id=product.id, name=slug, color="clear")
    db_session.add(variant)
    db_session.flush()
    sku = SKU(variant_id=variant.id, sku_code=f"SKU-{slug}", retail_price=price, currency="USD")
    db_session.add(sku)
    db_session.flush()
    db_session.add(Inventory(sku_id=sku.id, warehouse_id=warehouse.id, stock=100, reserved=0))
    db_session.commit()
    return sku


def _cart(db_session, *skus_qty):
    cart = Cart(token=f"t-{uuid.uuid4().hex}")
    db_session.add(cart)
    db_session.flush()
    for sku, qty in skus_qty:
        db_session.add(CartItem(cart_id=cart.id, sku_id=sku.id, quantity=qty))
    db_session.commit()
    db_session.refresh(cart)
    return cart


def _order(db_session, cart, user=None, **over):
    payload = {**CHECKOUT_PAYLOAD, **over}
    order = create_order(db_session, cart, CheckoutRequest(**payload), user)
    db_session.commit()
    return order


def _tax(db_session, rate, tax_class="*", min_order=0, country="Uzbekistan"):
    db_session.add(TaxRule(country=country, region="*", customer_type="*", tax_type="vat", tax_class=tax_class, rate=rate, min_order_amount=min_order))
    db_session.commit()


# ---------------------------------------------------------------- product-level tax

def test_each_line_is_taxed_by_its_product_class(db_session, warehouse, sku):
    _tax(db_session, 12)                    # general rule
    _tax(db_session, 5, tax_class="reduced")
    reduced = _add_product(db_session, warehouse, "reduced-item", 100, "reduced")
    zero = _add_product(db_session, warehouse, "zero-item", 100, "zero")
    exempt = _add_product(db_session, warehouse, "exempt-item", 100, "exempt")

    order = _order(db_session, _cart(db_session, (sku, 10), (reduced, 1), (zero, 1), (exempt, 1)))  # sku = 10 USD each
    taxes = {i.sku_code_snapshot: i.tax_amount for i in order.items}
    assert taxes == {
        "SKU-1000-001": Decimal("12.00"),   # 100 * 12%
        "SKU-reduced-item": Decimal("5.00"),
        "SKU-zero-item": Decimal("0.00"),
        "SKU-exempt-item": Decimal("0.00"),
    }
    assert order.tax_amount == Decimal("17.00")
    assert order.total_amount == order.subtotal_amount + order.delivery_amount + order.tax_amount - order.discount_amount


def test_reduced_falls_back_to_the_general_rule_when_no_reduced_rule_exists(db_session, warehouse, sku):
    _tax(db_session, 12)
    reduced = _add_product(db_session, warehouse, "r", 100, "reduced")
    order = _order(db_session, _cart(db_session, (reduced, 1)))
    assert order.tax_amount == Decimal("12.00")


def test_order_value_tier_uses_the_whole_cart_and_discount_lowers_the_taxable_amount(db_session, warehouse, sku):
    _tax(db_session, 10)
    _tax(db_session, 20, min_order=150)  # tier from 150 USD of taxable goods
    a = _add_product(db_session, warehouse, "a", 100)
    b = _add_product(db_session, warehouse, "b", 100, "exempt")
    # 200 total qualifies the 20% tier, but only the taxable (non-exempt) line pays it
    order = _order(db_session, _cart(db_session, (a, 1), (b, 1)))
    assert order.tax_amount == Decimal("20.00")


def test_admin_can_set_class_on_product_and_rule(client, db_session, sku):
    from app.models.enums import UserRole
    from conftest import login, make_admin

    make_admin(db_session, "root@example.com", UserRole.SUPER_ADMIN)
    h = login(client, "root@example.com")
    r = client.patch(f"/api/v1/admin/products/{sku.variant.product_id}", json={"tax_class": "reduced"}, headers=h)
    assert r.status_code == 200 and client.get(f"/api/v1/products/{sku.variant.product.slug}").json()["tax_class"] == "reduced"
    assert client.patch(f"/api/v1/admin/products/{sku.variant.product_id}", json={"tax_class": "bogus"}, headers=h).status_code == 422

    r = client.post("/api/v1/admin/tax-rules/", json={"country": "Uzbekistan", "customer_type": "*", "rate": "5", "tax_class": "reduced"}, headers=h)
    assert r.status_code == 201 and r.json()["tax_class"] == "reduced"
    # same keys but a different class is a different rule
    assert client.post("/api/v1/admin/tax-rules/", json={"country": "Uzbekistan", "customer_type": "*", "rate": "12"}, headers=h).status_code == 201


# ---------------------------------------------------------------- promo targeting

def _promo(db_session, code="SAVE", value=10, **kw):
    promo = PromoCode(code=code, discount_type=PromoDiscountType.PERCENT, discount_value=value, **kw)
    db_session.add(promo)
    db_session.commit()
    return promo


def test_product_targeted_promo_discounts_only_matching_lines(db_session, warehouse, sku):
    other = _add_product(db_session, warehouse, "other", 100)
    _promo(db_session, value=50, product_ids=[sku.variant.product_id])
    order = _order(db_session, _cart(db_session, (sku, 10), (other, 1)), promo_code="SAVE")  # 100 + 100
    by_sku = {i.sku_code_snapshot: i.discount_amount for i in order.items}
    assert by_sku == {"SKU-1000-001": Decimal("50.00"), "SKU-other": Decimal("0.00")}
    assert order.discount_amount == Decimal("50.00")


def test_category_targeting_includes_subcategories(db_session, warehouse, sku):
    parent = db_session.query(Category).first()
    child = Category(name="Lids", slug="lids", parent_id=parent.id)
    db_session.add(child)
    db_session.commit()
    in_child = _add_product(db_session, warehouse, "lid", 100, category=child)
    other_cat = Category(name="Other", slug="other-cat")
    db_session.add(other_cat)
    db_session.commit()
    outside = _add_product(db_session, warehouse, "outside", 100, category=other_cat)
    _promo(db_session, value=10, category_ids=[parent.id])

    order = _order(db_session, _cart(db_session, (in_child, 1), (outside, 1)), promo_code="SAVE")
    assert {i.sku_code_snapshot: i.discount_amount for i in order.items} == {"SKU-lid": Decimal("10.00"), "SKU-outside": Decimal("0.00")}


def test_targeted_promo_is_rejected_when_nothing_in_the_cart_matches(db_session, warehouse, sku):
    other = _add_product(db_session, warehouse, "other", 100)
    _promo(db_session, product_ids=[sku.variant.product_id])
    with pytest.raises(OrderError, match="does not apply"):
        create_order(db_session, _cart(db_session, (other, 1)), CheckoutRequest(**{**CHECKOUT_PAYLOAD, "promo_code": "SAVE"}), None)
    db_session.rollback()


def test_minimum_order_counts_only_matching_lines(db_session, warehouse, sku):
    other = _add_product(db_session, warehouse, "other", 1000)
    _promo(db_session, product_ids=[sku.variant.product_id], min_order_amount=50)
    with pytest.raises(OrderError, match="at least"):
        create_order(db_session, _cart(db_session, (sku, 1), (other, 1)), CheckoutRequest(**{**CHECKOUT_PAYLOAD, "promo_code": "SAVE"}), None)  # 10 matching < 50
    db_session.rollback()


def test_discount_shares_add_up_exactly(db_session, warehouse, sku):
    a = _add_product(db_session, warehouse, "a", Decimal("3.33"))
    b = _add_product(db_session, warehouse, "b", Decimal("3.33"))
    _promo(db_session, value=Decimal("10"), product_ids=[a.variant.product_id, b.variant.product_id])
    order = _order(db_session, _cart(db_session, (a, 1), (b, 1), (sku, 1)), promo_code="SAVE")
    assert sum(i.discount_amount for i in order.items) == order.discount_amount == Decimal("0.67")


# ---------------------------------------------------------------- per-customer limit

def test_per_customer_limit_by_email_and_released_on_cancel(db_session, warehouse, sku):
    _promo(db_session, max_uses_per_customer=1)
    first = _order(db_session, _cart(db_session, (sku, 1)), promo_code="SAVE", email="Bob@example.com")

    with pytest.raises(OrderError, match="already used"):
        create_order(db_session, _cart(db_session, (sku, 1)), CheckoutRequest(**{**CHECKOUT_PAYLOAD, "promo_code": "SAVE", "email": "bob@example.com"}), None)
    db_session.rollback()

    # a different customer is fine
    _order(db_session, _cart(db_session, (sku, 1)), promo_code="SAVE", email="carol@example.com")

    # cancelling the first order gives Bob his use back
    set_order_status(db_session, first, OrderStatus.CANCELLED, None)
    _order(db_session, _cart(db_session, (sku, 1)), promo_code="SAVE", email="bob@example.com")


def test_cart_preview_shows_targeted_discount_and_per_line_tax(client, db_session, warehouse, sku):
    _tax(db_session, 10)
    other = _add_product(db_session, warehouse, "other", 100, "exempt")
    _promo(db_session, value=50, product_ids=[sku.variant.product_id])
    h = {}
    tok = client.get("/api/v1/cart/").headers.get("x-cart-token") or client.get("/api/v1/cart/").json().get("token")
    for s, q in ((sku, 10), (other, 1)):
        r = client.post("/api/v1/cart/items", json={"sku_id": s.id, "quantity": q}, headers={"X-Cart-Token": tok} if tok else {})
        assert r.status_code in (200, 201), r.text
    r = client.get("/api/v1/cart/?promo_code=SAVE&country=Uzbekistan", headers={"X-Cart-Token": tok} if tok else {})
    assert r.status_code == 200, r.text
    body = r.json()
    assert Decimal(str(body["discount"])) == Decimal("50.00")
    assert Decimal(str(body["tax"])) == Decimal("5.00")  # (100 - 50) * 10%, the exempt line pays nothing


# ---------------------------------------------------------------- country and customer lists (PRD ТЗ№1 §23)

def test_country_list_restricts_where_the_code_works(db_session, warehouse, sku):
    _promo(db_session, countries=["kazakhstan", "Uzbekistan"])
    order = _order(db_session, _cart(db_session, (sku, 1)), promo_code="SAVE")  # CHECKOUT_PAYLOAD ships to Uzbekistan
    assert order.discount_amount == Decimal("1.00")
    with pytest.raises(OrderError, match="delivery country"):
        create_order(db_session, _cart(db_session, (sku, 1)), CheckoutRequest(**{**CHECKOUT_PAYLOAD, "promo_code": "SAVE", "country": "Germany"}), None)
    db_session.rollback()


def test_customer_list_limits_the_code_to_named_accounts(client, db_session, warehouse, sku):
    from app.models.user import User
    from conftest import register

    register(client, "vip@example.com")
    register(client, "other@example.com")
    vip = db_session.query(User).filter_by(email="vip@example.com").one()
    other = db_session.query(User).filter_by(email="other@example.com").one()
    _promo(db_session, customer_ids=[vip.id])

    assert _order(db_session, _cart(db_session, (sku, 1)), user=vip, promo_code="SAVE").discount_amount == Decimal("1.00")
    for who in (other, None):  # another account, and a guest
        with pytest.raises(OrderError, match="not available for your account"):
            create_order(db_session, _cart(db_session, (sku, 1)), CheckoutRequest(**{**CHECKOUT_PAYLOAD, "promo_code": "SAVE"}), who)
        db_session.rollback()


def test_admin_api_saves_the_lists(client, db_session, sku):
    from app.models.enums import UserRole
    from conftest import login, make_admin

    make_admin(db_session, "mk@example.com", UserRole.MARKETING_MANAGER)
    h = login(client, "mk@example.com")
    r = client.post("/api/v1/admin/promo-codes/", json={"code": "KZ10", "discount_type": "percent", "discount_value": "10", "countries": ["Kazakhstan"], "customer_ids": [5, 7]}, headers=h)
    assert r.status_code == 201, r.text
    assert r.json()["countries"] == ["Kazakhstan"] and r.json()["customer_ids"] == [5, 7]
    assert client.patch(f"/api/v1/admin/promo-codes/{r.json()['id']}", json={"countries": []}, headers=h).json()["countries"] is None  # empty = no restriction
