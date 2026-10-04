"""Tax engine wildcard lookup (PRD ТЗ№3 §41) and its admin CRUD."""

from decimal import Decimal

from app.models.enums import UserRole
from app.models.tax_rule import TaxRule
from app.services.tax import calculate_tax
from conftest import login, make_admin


def test_unconfigured_jurisdiction_is_zero_tax_not_an_error(db_session):
    assert calculate_tax(db_session, "Nowhere", "retail", Decimal("100")) == Decimal("0.00")


def test_exact_match_and_wildcard_fallbacks(db_session):
    db_session.add_all(
        [
            TaxRule(country="Uzbekistan", customer_type="retail", tax_type="vat", rate=Decimal("12.00")),
            TaxRule(country="Germany", customer_type="*", tax_type="vat", rate=Decimal("19.00")),
            TaxRule(country="*", customer_type="distributor", tax_type="vat", rate=Decimal("5.00")),
        ]
    )
    db_session.commit()

    assert calculate_tax(db_session, "Uzbekistan", "retail", Decimal("100")) == Decimal("12.00")
    assert calculate_tax(db_session, "Germany", "wholesale", Decimal("200")) == Decimal("38.00")
    assert calculate_tax(db_session, "France", "distributor", Decimal("1000")) == Decimal("50.00")


def test_inactive_rule_is_ignored(db_session):
    rule = TaxRule(country="Uzbekistan", customer_type="retail", tax_type="vat", rate=Decimal("12.00"), is_active=False)
    db_session.add(rule)
    db_session.commit()
    assert calculate_tax(db_session, "Uzbekistan", "retail", Decimal("100")) == Decimal("0.00")


def test_admin_tax_rule_crud(client, db_session):
    make_admin(db_session, "accountant@example.com", UserRole.ACCOUNTANT)
    headers = login(client, "accountant@example.com")

    r = client.post(
        "/api/v1/admin/tax-rules/", headers=headers,
        json={"country": "Uzbekistan", "customer_type": "retail", "rate": "12.00"},
    )
    assert r.status_code == 201, r.text
    rule_id = r.json()["id"]

    r = client.post(
        "/api/v1/admin/tax-rules/", headers=headers,
        json={"country": "Uzbekistan", "customer_type": "retail", "rate": "5.00"},
    )
    assert r.status_code == 400  # duplicate (country, customer_type, tax_type)

    r = client.patch(f"/api/v1/admin/tax-rules/{rule_id}", headers=headers, json={"rate": "15.00"})
    assert r.status_code == 200 and r.json()["rate"] == "15.00"

    r = client.get("/api/v1/admin/tax-rules/", headers=headers)
    assert len(r.json()) == 1


def test_region_rule_beats_country_rule_and_falls_back(db_session):
    db_session.add_all(
        [
            TaxRule(country="USA", customer_type="*", tax_type="vat", rate=Decimal("0.00")),
            TaxRule(country="USA", region="California", customer_type="*", tax_type="vat", rate=Decimal("7.25")),
        ]
    )
    db_session.commit()

    assert calculate_tax(db_session, "USA", "retail", Decimal("100"), region="California") == Decimal("7.25")
    assert calculate_tax(db_session, "USA", "retail", Decimal("100"), region=" california ") == Decimal("7.25")
    assert calculate_tax(db_session, "USA", "retail", Decimal("100"), region="Texas") == Decimal("0.00")
    assert calculate_tax(db_session, "USA", "retail", Decimal("100")) == Decimal("0.00")


def test_region_rule_does_not_apply_without_that_region(db_session):
    db_session.add(TaxRule(country="USA", region="California", customer_type="*", tax_type="vat", rate=Decimal("7.25")))
    db_session.commit()
    assert calculate_tax(db_session, "USA", "retail", Decimal("100")) == Decimal("0.00")


def test_order_value_tiers_pick_the_highest_reached_minimum(db_session):
    db_session.add_all(
        [
            TaxRule(country="Germany", customer_type="*", tax_type="vat", rate=Decimal("19.00")),
            TaxRule(country="Germany", customer_type="*", tax_type="vat", rate=Decimal("7.00"), min_order_amount=Decimal("500")),
        ]
    )
    db_session.commit()

    assert calculate_tax(db_session, "Germany", "retail", Decimal("100")) == Decimal("19.00")
    assert calculate_tax(db_session, "Germany", "retail", Decimal("500")) == Decimal("35.00")
    assert calculate_tax(db_session, "Germany", "retail", Decimal("1000")) == Decimal("70.00")


def test_order_value_minimum_is_compared_in_usd(db_session):
    from app.models.exchange_rate import ExchangeRate

    db_session.add(ExchangeRate(currency="UZS", units_per_usd=Decimal("10000")))
    db_session.add_all(
        [
            TaxRule(country="Uzbekistan", customer_type="*", tax_type="vat", rate=Decimal("12.00")),
            TaxRule(country="Uzbekistan", customer_type="*", tax_type="vat", rate=Decimal("6.00"), min_order_amount=Decimal("100")),
        ]
    )
    db_session.commit()

    # 500,000 UZS = 50 USD: below the 100 USD tier.
    assert calculate_tax(db_session, "Uzbekistan", "retail", Decimal("500000"), currency="UZS") == Decimal("60000.00")
    # 2,000,000 UZS = 200 USD: reaches it.
    assert calculate_tax(db_session, "Uzbekistan", "retail", Decimal("2000000"), currency="UZS") == Decimal("120000.00")


def test_admin_can_create_region_and_tier_rules(client, db_session):
    make_admin(db_session, "acct@example.com", UserRole.ACCOUNTANT)
    headers = login(client, "acct@example.com")
    body = {"country": "USA", "region": "Texas", "customer_type": "*", "rate": "6.25", "min_order_amount": "50"}
    r = client.post("/api/v1/admin/tax-rules/", json=body, headers=headers)
    assert r.status_code == 201, r.text
    assert r.json()["region"] == "Texas" and Decimal(r.json()["min_order_amount"]) == Decimal("50")
    assert client.post("/api/v1/admin/tax-rules/", json=body, headers=headers).status_code == 400
    assert client.post("/api/v1/admin/tax-rules/", json={**body, "min_order_amount": "100"}, headers=headers).status_code == 201


def test_checkout_uses_and_stores_region(db_session, sku):
    from app.models.cart import Cart
    from app.models.cart_item import CartItem
    from app.schemas.order import CheckoutRequest
    from app.services.order_service import create_order
    from conftest import CHECKOUT_PAYLOAD

    db_session.add(TaxRule(country="Uzbekistan", region="Tashkent", customer_type="*", tax_type="vat", rate=Decimal("10.00")))
    cart = Cart(token="tax-region")
    db_session.add(cart)
    db_session.flush()
    db_session.add(CartItem(cart_id=cart.id, sku_id=sku.id, quantity=2))
    db_session.commit()
    db_session.refresh(cart)

    order = create_order(db_session, cart, CheckoutRequest(**{**CHECKOUT_PAYLOAD, "region": "Tashkent"}), None)
    assert order.region == "Tashkent"
    assert order.tax_amount == Decimal("2.00")  # 10% of 2 x 10 USD
