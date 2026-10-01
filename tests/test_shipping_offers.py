"""Free-shipping threshold, cart progress and the product-page delivery estimate."""

from decimal import Decimal

from app.models.exchange_rate import ExchangeRate
from app.models.shipping_rate import ShippingRate
from conftest import CHECKOUT_PAYLOAD, register


def _set_rate(db_session, **fields):
    rate = db_session.query(ShippingRate).one()
    for key, value in fields.items():
        setattr(rate, key, value)
    db_session.commit()
    return rate


def _cart(client, sku, quantity, headers=None):
    return client.post("/api/v1/cart/items", headers=headers or {}, json={"sku_id": sku.id, "quantity": quantity})


def test_shipping_is_free_at_or_above_threshold_and_charged_below(client, sku, db_session):
    _set_rate(db_session, base_fee=5, free_shipping_threshold=30)  # sku costs 10 USD
    headers = register(client, "free1@example.com")

    _cart(client, sku, 2, headers)  # 20 < 30
    below = client.get("/api/v1/cart/?country=Uzbekistan&delivery_method=*", headers=headers).json()
    assert Decimal(below["delivery"]) == Decimal("5.00")
    assert Decimal(below["free_shipping_threshold"]) == Decimal("30")
    assert Decimal(below["free_shipping_remaining"]) == Decimal("10")

    _cart(client, sku, 1, headers)  # 30 == threshold
    at = client.get("/api/v1/cart/?country=Uzbekistan&delivery_method=*", headers=headers).json()
    assert Decimal(at["delivery"]) == Decimal("0.00")
    assert Decimal(at["free_shipping_remaining"]) == Decimal("0")


def test_checkout_honours_the_threshold(client, sku, db_session):
    _set_rate(db_session, base_fee=5, free_shipping_threshold=20)
    headers = register(client, "free2@example.com")
    _cart(client, sku, 2, headers)
    r = client.post("/api/v1/orders/", headers=headers, json=CHECKOUT_PAYLOAD)
    assert r.status_code == 201, r.text
    assert Decimal(r.json()["delivery_amount"]) == Decimal("0.00")


def test_threshold_is_measured_after_discount(client, sku, db_session):
    from app.models.promo_code import PromoCode, PromoDiscountType

    _set_rate(db_session, base_fee=5, free_shipping_threshold=20)
    db_session.add(PromoCode(code="HALF", discount_type=PromoDiscountType.PERCENT, discount_value=50, is_active=True))
    db_session.commit()
    headers = register(client, "free3@example.com")
    _cart(client, sku, 2, headers)  # 20 -> 10 after promo, below threshold
    cart = client.get("/api/v1/cart/?promo_code=HALF&country=Uzbekistan&delivery_method=*", headers=headers).json()
    assert Decimal(cart["delivery"]) == Decimal("5.00")


def test_threshold_in_another_currency_is_converted(client, sku, db_session):
    db_session.add(ExchangeRate(currency="UZS", units_per_usd=Decimal("10000")))
    _set_rate(db_session, base_fee=5, currency="USD", free_shipping_threshold=30)
    db_session.commit()
    headers = register(client, "free4@example.com")
    _cart(client, sku, 1, headers)
    client.patch("/api/v1/cart/currency", headers=headers, json={"currency": "UZS"})
    cart = client.get("/api/v1/cart/", headers=headers).json()
    assert cart["currency"] == "UZS"
    assert Decimal(cart["free_shipping_threshold"]) == Decimal("300000.00")


def test_no_offer_means_no_progress_fields(client, sku):
    headers = register(client, "free5@example.com")
    _cart(client, sku, 1, headers)
    cart = client.get("/api/v1/cart/", headers=headers).json()
    assert cart["free_shipping_threshold"] is None and cart["free_shipping_remaining"] is None


def test_estimate_prefers_country_specific_rate(client, db_session):
    db_session.add(ShippingRate(country="*", delivery_method="*", base_fee=0, per_kg_fee=0, min_delivery_days=7, max_delivery_days=14))
    db_session.add(ShippingRate(country="Uzbekistan", delivery_method="courier", base_fee=0, per_kg_fee=0, min_delivery_days=1, max_delivery_days=3))
    db_session.commit()
    uz = client.get("/api/v1/shipping/estimate?country=Uzbekistan").json()
    assert (uz["min_days"], uz["max_days"]) == (1, 3)
    other = client.get("/api/v1/shipping/estimate?country=Kazakhstan").json()
    assert (other["min_days"], other["max_days"]) == (7, 14)


def test_estimate_is_empty_when_no_days_configured(client, sku):
    assert client.get("/api/v1/shipping/estimate?country=Uzbekistan").json()["max_days"] is None


def test_admin_rejects_inverted_days_and_accepts_offer_fields(client, db_session):
    from app.models.enums import UserRole
    from conftest import login, make_admin

    make_admin(db_session, "shipadmin@example.com", UserRole.SALES_MANAGER)
    headers = login(client, "shipadmin@example.com")
    bad = client.post(
        "/api/v1/admin/shipping-rates/", headers=headers,
        json={"country": "X", "delivery_method": "y", "min_delivery_days": 5, "max_delivery_days": 2},
    )
    assert bad.status_code == 422
    ok = client.post(
        "/api/v1/admin/shipping-rates/", headers=headers,
        json={"country": "X", "delivery_method": "y", "min_delivery_days": 2, "max_delivery_days": 5, "free_shipping_threshold": "100"},
    )
    assert ok.status_code == 201, ok.text
    assert ok.json()["max_delivery_days"] == 5


def test_estimate_reports_availability_and_cheapest_fee(client, db_session):
    from decimal import Decimal

    from app.models.shipping_rate import ShippingRate

    db_session.add_all(
        [
            ShippingRate(country="Uzbekistan", delivery_method="courier", base_fee=Decimal("5"), currency="USD", max_delivery_days=3),
            ShippingRate(country="Uzbekistan", delivery_method="pickup", base_fee=Decimal("0"), currency="USD"),
            ShippingRate(country="Germany", delivery_method="courier", base_fee=Decimal("20"), currency="USD", min_delivery_days=5, max_delivery_days=9),
        ]
    )
    db_session.commit()

    uz = client.get("/api/v1/shipping/estimate", params={"country": "Uzbekistan"}).json()
    # The free "pickup" method does not make delivery look free: the fee is the courier's.
    assert uz["available"] is True and Decimal(uz["from_fee"]) == 5 and uz["max_days"] == 3 and uz["fee_currency"] == "USD"
    de = client.get("/api/v1/shipping/estimate", params={"country": "Germany"}).json()
    assert Decimal(de["from_fee"]) == 20 and (de["min_days"], de["max_days"]) == (5, 9)
    nowhere = client.get("/api/v1/shipping/estimate", params={"country": "Atlantis"}).json()
    assert nowhere["available"] is False and nowhere["from_fee"] is None
