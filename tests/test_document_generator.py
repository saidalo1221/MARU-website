"""PRD ТЗ№1 §57: confirmation, invoice, proforma invoice and packing list are generated automatically."""

import re

from app.models.enums import OrderStatus, UserRole
from app.models.order_document import OrderDocument
from app.schemas.order import CheckoutRequest
from app.services import document_generator
from app.services.order_service import create_order, set_order_status
from conftest import CHECKOUT_PAYLOAD, login, make_admin
from test_orders_reservation import _cart_with


def _docs(db_session, order):
    db_session.expire_all()
    return {d.doc_type: d for d in db_session.query(OrderDocument).filter_by(order_id=order.id, status="issued")}


def _place(db_session, sku, qty=2, **over):
    order = create_order(db_session, _cart_with(db_session, sku, qty), CheckoutRequest(**{**CHECKOUT_PAYLOAD, **over}), None)
    db_session.commit()
    return order


def test_documents_appear_at_the_right_moments(db_session, sku):
    order = _place(db_session, sku)
    document_generator.generate_for_status(db_session, order, None)  # what the checkout route does after commit
    assert set(_docs(db_session, order)) == {"order_confirmation"}

    set_order_status(db_session, order, OrderStatus.PAID, None)
    assert set(_docs(db_session, order)) == {"order_confirmation", "invoice"}
    set_order_status(db_session, order, OrderStatus.PROCESSING, None)
    set_order_status(db_session, order, OrderStatus.PACKED, None)
    assert "packing_list" in _docs(db_session, order)
    # asking again does not pile up copies
    document_generator.generate_for_status(db_session, order, OrderStatus.PAID)
    assert db_session.query(OrderDocument).filter_by(order_id=order.id, doc_type="invoice").count() == 1


def test_company_orders_get_a_proforma_with_company_details_and_everything_is_escaped(db_session, sku):
    order = _place(
        db_session, sku, order_type="company", company_name="<script>alert(1)</script> LLC", company_tax_number="TX-123",
        company_reg_number="REG-9", contact_person="Ali & Co", company_address="1 Main St",
    )
    document_generator.generate_for_status(db_session, order, None)
    docs = _docs(db_session, order)
    assert {"order_confirmation", "proforma_invoice"} <= set(docs)
    from app.services import documents

    page = documents.path_of(docs["proforma_invoice"].storage_name).read_text(encoding="utf-8")
    assert "Proforma invoice" in page and "TX-123" in page and "REG-9" in page and "not a tax document" in page
    assert "<script>" not in page and "&lt;script&gt;alert(1)&lt;/script&gt; LLC" in page and "Ali &amp; Co" in page
    assert order.order_number in page and "SKU-1000-001" in page


def test_invoice_totals_and_packing_list_has_no_prices(db_session, sku):
    sku.unit_weight_g, sku.box_quantity, sku.box_weight_g = 20, 4, 100
    sku.box_length_mm = sku.box_width_mm = sku.box_height_mm = 100
    db_session.commit()
    order = _place(db_session, sku, qty=9)
    set_order_status(db_session, order, OrderStatus.PAID, None)
    set_order_status(db_session, order, OrderStatus.PROCESSING, None)
    set_order_status(db_session, order, OrderStatus.PACKED, None)
    from app.services import documents

    docs = _docs(db_session, order)
    invoice = documents.path_of(docs["invoice"].storage_name).read_text(encoding="utf-8")
    assert f"{float(order.total_amount):,.2f}" in invoice and "Payment:" in invoice
    packing = documents.path_of(docs["packing_list"].storage_name).read_text(encoding="utf-8")
    assert "3 box(es)" in packing and "USD 10.00" not in packing and "Unit price" not in packing


def test_admin_regenerates_and_customer_opens_it_sandboxed(client, db_session, sku):
    order = _place(db_session, sku)
    make_admin(db_session, "sales@example.com", UserRole.SALES_MANAGER)
    h = login(client, "sales@example.com")
    first = client.post(f"/api/v1/admin/orders/{order.id}/documents/generate", json={"doc_type": "invoice"}, headers=h)
    assert first.status_code == 201, first.text
    second = client.post(f"/api/v1/admin/orders/{order.id}/documents/generate", json={"doc_type": "invoice"}, headers=h)
    assert second.json()["id"] != first.json()["id"]
    assert client.post(f"/api/v1/admin/orders/{order.id}/documents/generate", json={"doc_type": "fiscal_receipt"}, headers=h).status_code == 400

    guest = {"X-Order-Token": order.guest_order_token}
    listing = client.get(f"/api/v1/orders/{order.id}/documents", headers=guest).json()
    assert [d["id"] for d in listing if d["doc_type"] == "invoice"] == [second.json()["id"]]  # the old copy is void
    link = client.post(f"/api/v1/orders/{order.id}/documents/{second.json()['id']}/link", headers=guest).json()["url"]
    page = client.get(re.sub(r"^https?://[^/]+", "", link))
    assert page.status_code == 200 and page.headers["content-type"].startswith("text/html")
    assert "sandbox" in page.headers["content-security-policy"] and page.headers["content-disposition"].startswith("inline")
