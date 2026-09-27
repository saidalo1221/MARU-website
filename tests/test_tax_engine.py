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
