"""Request a Quote and Quote -> Order conversion (PRD ТЗ№2 §32, ТЗ№4 §16/§85)."""

from app.models.enums import UserRole
from app.models.quote_request import QuoteRequest, QuoteStatus
from conftest import login, make_admin


def test_create_quote_gets_rfq_number(client):
    r = client.post(
        "/api/v1/quotes/",
        json={
            "request_type": "wholesale", "name": "John Smith", "company": "Acme LLC",
            "country": "Germany", "city": "Berlin", "email": "john@acme.example",
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["rfq_number"].startswith("RFQ-")


def test_convert_quote_requires_accepted_status_and_price(client, db_session):
    make_admin(db_session, "sales@example.com", UserRole.SALES_MANAGER)
    headers = login(client, "sales@example.com")

    quote = QuoteRequest(
        rfq_number="RFQ-2026-000001", request_type="wholesale", name="John Smith", company="Acme LLC",
        country="Germany", city="Berlin", email="john@acme.example", status=QuoteStatus.NEW,
    )
    db_session.add(quote)
    db_session.commit()

    r = client.post(
        f"/api/v1/admin/quotes/{quote.id}/convert", headers=headers,
        json={"address_line": "Main St 1", "postal_code": "10115"},
    )
    assert r.status_code == 400
    assert "ACCEPTED" in r.json()["detail"]

    quote.status = QuoteStatus.ACCEPTED
    db_session.commit()

    r = client.post(
        f"/api/v1/admin/quotes/{quote.id}/convert", headers=headers,
        json={"address_line": "Main St 1", "postal_code": "10115"},
    )
    assert r.status_code == 400
    assert "proposed_price" in r.json()["detail"]


def test_convert_quote_creates_order_with_snapshotted_price(client, db_session):
    make_admin(db_session, "sales2@example.com", UserRole.SALES_MANAGER)
    headers = login(client, "sales2@example.com")

    quote = QuoteRequest(
        rfq_number="RFQ-2026-000002", request_type="wholesale", name="John Smith", company="Acme LLC",
        country="Germany", city="Berlin", email="john@acme.example", status=QuoteStatus.ACCEPTED,
        proposed_price=4500, currency="EUR", products="1000ml containers", quantity="5000 units",
    )
    db_session.add(quote)
    db_session.commit()

    r = client.post(
        f"/api/v1/admin/quotes/{quote.id}/convert", headers=headers,
        json={"address_line": "Main St 1", "postal_code": "10115", "delivery_method": "freight"},
    )
    assert r.status_code == 201, r.text
    order = r.json()
    assert order["order_type"] == "company"
    assert float(order["total_amount"]) == 4500.0
    assert order["currency"] == "EUR"
    assert order["first_name"] == "John" and order["last_name"] == "Smith"
    assert len(order["items"]) == 1

    db_session.refresh(quote)
    assert quote.order_id == order["id"]

    # Converting the same (already-converted) quote again is rejected.
    r = client.post(
        f"/api/v1/admin/quotes/{quote.id}/convert", headers=headers,
        json={"address_line": "Main St 1", "postal_code": "10115"},
    )
    assert r.status_code == 400
    assert "already converted" in r.json()["detail"]
