"""Multi-warehouse stock aggregation and single-warehouse-per-line
reservation (PRD ТЗ№3 §27/§28/§68)."""

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.inventory import Inventory
from app.models.shipping_rate import ShippingRate
from app.models.sku import SKU
from app.models.warehouse import Warehouse
from app.schemas.order import CheckoutRequest
from app.services.order_service import InsufficientStockError, OrderError, available_stock, create_order
from conftest import CHECKOUT_PAYLOAD


def _two_warehouse_sku(db_session):
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
    db_session.flush()
    sku = SKU(variant_id=variant.id, sku_code="SKU-1000-002", retail_price=10, currency="USD")
    db_session.add(sku)
    db_session.flush()

    preferred = Warehouse(name="Tashkent", country="Uzbekistan", priority=1)
    backup = Warehouse(name="Samarkand", country="Uzbekistan", priority=2)
    db_session.add_all([preferred, backup])
    db_session.flush()

    inv_preferred = Inventory(sku_id=sku.id, warehouse_id=preferred.id, stock=3, reserved=0)
    inv_backup = Inventory(sku_id=sku.id, warehouse_id=backup.id, stock=10, reserved=0)
    db_session.add_all([inv_preferred, inv_backup])
    db_session.add(ShippingRate(country="*", delivery_method="*", base_fee=0, per_kg_fee=0))
    db_session.commit()
    return sku, preferred, backup, inv_preferred, inv_backup


def _cart_with(db_session, sku, quantity):
    cart = Cart(token=f"tok-{sku.id}-{quantity}-{id(object())}")
    db_session.add(cart)
    db_session.flush()
    db_session.add(CartItem(cart_id=cart.id, sku_id=sku.id, quantity=quantity))
    db_session.commit()
    db_session.refresh(cart)
    return cart


def test_available_stock_aggregates_across_warehouses(db_session):
    sku, *_ = _two_warehouse_sku(db_session)
    assert available_stock(db_session, sku.id) == 13
    db_session.refresh(sku)
    assert sku.available_quantity == 13


def test_reservation_prefers_higher_priority_warehouse(db_session):
    sku, preferred, backup, inv_preferred, inv_backup = _two_warehouse_sku(db_session)
    cart = _cart_with(db_session, sku, 2)
    order = create_order(db_session, cart, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()

    assert order.items[0].warehouse_id == preferred.id
    db_session.refresh(inv_preferred)
    db_session.refresh(inv_backup)
    assert inv_preferred.reserved == 2
    assert inv_backup.reserved == 0


def test_line_too_big_for_preferred_warehouse_falls_through_entirely(db_session):
    sku, preferred, backup, inv_preferred, inv_backup = _two_warehouse_sku(db_session)
    cart = _cart_with(db_session, sku, 5)  # doesn't fit in preferred (stock=3)
    order = create_order(db_session, cart, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()

    assert order.items[0].warehouse_id == backup.id
    db_session.refresh(inv_preferred)
    db_session.refresh(inv_backup)
    assert inv_preferred.reserved == 0
    assert inv_backup.reserved == 5


def test_no_single_warehouse_can_cover_line_even_if_aggregate_can(db_session):
    """3 + 10 = 13 available in aggregate, but nothing can satisfy a line of
    14 alone -> rejected. This is deliberate (single-warehouse-per-line,
    not split fulfillment) — see order_service._reserve_stock()'s docstring."""
    sku, *_ = _two_warehouse_sku(db_session)
    cart = _cart_with(db_session, sku, 14)
    try:
        create_order(db_session, cart, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
        assert False, "expected OrderError/InsufficientStockError"
    except (OrderError, InsufficientStockError):
        db_session.rollback()


def test_inactive_warehouse_excluded_from_availability(db_session):
    sku, preferred, backup, inv_preferred, inv_backup = _two_warehouse_sku(db_session)
    backup.is_active = False
    db_session.commit()
    assert available_stock(db_session, sku.id) == 3
