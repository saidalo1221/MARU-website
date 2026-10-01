"""Edge cases from the PRD audit: minimum order quantity, promo currency and
atomic promo redemption."""

from decimal import Decimal

import pytest

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.exchange_rate import ExchangeRate
from app.models.promo_code import PromoCode, PromoDiscountType
from app.schemas.order import CheckoutRequest
from app.services.order_service import OrderError, create_order
from app.services.pricing import PromoCodeError, redeem_promo, validate_promo
from conftest import CHECKOUT_PAYLOAD


def _cart(db_session, sku, quantity, currency="USD"):
    cart = Cart(token=f"tok-{id(object())}", currency=currency)
    db_session.add(cart)
    db_session.flush()
    db_session.add(CartItem(cart_id=cart.id, sku_id=sku.id, quantity=quantity))
    db_session.commit()
    db_session.refresh(cart)
    return cart


def _checkout(**extra):
    return CheckoutRequest(**{**CHECKOUT_PAYLOAD, **extra})


def _promo(db_session, **fields):
    promo = PromoCode(code="SAVE", is_active=True, **fields)
    db_session.add(promo)
    db_session.commit()
    return promo


def test_checkout_rejects_quantity_below_product_minimum(db_session, sku):
    sku.variant.product.min_order_quantity = 5
    db_session.commit()

    with pytest.raises(OrderError, match="MIN_ORDER_QUANTITY"):
        create_order(db_session, _cart(db_session, sku, 4), _checkout(), None)

    order = create_order(db_session, _cart(db_session, sku, 5), _checkout(), None)
    assert order.items[0].quantity == 5


def test_fixed_promo_and_minimum_are_converted_from_promo_currency(db_session, sku):
    db_session.add(ExchangeRate(currency="UZS", units_per_usd=Decimal("10000")))
    # 5 USD off, with a 20 USD minimum, against a cart priced in UZS.
    _promo(
        db_session,
        discount_type=PromoDiscountType.FIXED,
        discount_value=Decimal("5"),
        currency="USD",
        min_order_amount=Decimal("20"),
    )

    # 1 x 10 USD = 100000 UZS, below the 200000 UZS minimum.
    with pytest.raises(OrderError, match="at least"):
        create_order(db_session, _cart(db_session, sku, 1, "UZS"), _checkout(promo_code="SAVE"), None)

    # 3 x 10 USD = 300000 UZS; the discount is 5 USD = 50000 UZS, not 5 UZS.
    order = create_order(db_session, _cart(db_session, sku, 3, "UZS"), _checkout(promo_code="SAVE"), None)
    assert order.subtotal_amount == Decimal("300000.00")
    assert order.discount_amount == Decimal("50000.00")


def test_promo_without_currency_is_used_as_is(db_session, sku):
    _promo(db_session, discount_type=PromoDiscountType.FIXED, discount_value=Decimal("5"), min_order_amount=0)
    order = create_order(db_session, _cart(db_session, sku, 2), _checkout(promo_code="SAVE"), None)
    assert order.discount_amount == Decimal("5.00")


def test_last_promo_use_cannot_be_taken_twice(db_session, sku):
    promo = _promo(
        db_session, discount_type=PromoDiscountType.PERCENT, discount_value=Decimal("10"), min_order_amount=0, max_uses=1
    )
    # Both "requests" validated while one use was left...
    assert validate_promo(db_session, "SAVE", Decimal("100")).id == promo.id
    redeem_promo(db_session, promo)
    assert promo.used_count == 1
    # ...but only the first can redeem it.
    with pytest.raises(PromoCodeError, match="usage limit"):
        redeem_promo(db_session, promo)
    assert promo.used_count == 1


def test_uncapped_promo_keeps_counting(db_session, sku):
    promo = _promo(
        db_session, discount_type=PromoDiscountType.PERCENT, discount_value=Decimal("10"), min_order_amount=0
    )
    redeem_promo(db_session, promo)
    redeem_promo(db_session, promo)
    assert promo.used_count == 2
