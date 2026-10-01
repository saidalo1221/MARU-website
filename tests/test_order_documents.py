"""PRD ТЗ№4 §81-83: order documents are private, access-controlled and served by signed link."""

import pytest

from app.config import settings
from app.models.enums import UserRole
from app.schemas.order import CheckoutRequest
from app.services import documents
from app.services.order_service import create_order
from conftest import CHECKOUT_PAYLOAD, login, make_admin
from test_orders_reservation import _cart_with

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


@pytest.fixture(autouse=True)
def _private_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DOCUMENTS_DIR", str(tmp_path))


def _setup(client, db_session, sku):
    order = create_order(db_session, _cart_with(db_session, sku, 1), CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    db_session.commit()
    make_admin(db_session, "sales@example.com", UserRole.SALES_MANAGER)
    return order, login(client, "sales@example.com")


def _upload(client, admin, order_id, content=PDF, ctype="application/pdf", doc_type="invoice"):
    return client.post(
        f"/api/v1/admin/orders/{order_id}/documents",
        files={"file": ("invoice.pdf", content, ctype)},
        data={"doc_type": doc_type, "external_id": "1C-INV-9"},
        headers=admin,
    )


def test_admin_uploads_and_customer_downloads_with_signed_link(client, db_session, sku, tmp_path):
    order, admin = _setup(client, db_session, sku)
    r = _upload(client, admin, order.id)
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["doc_type"] == "invoice" and doc["external_id"] == "1C-INV-9"
    assert list(tmp_path.iterdir())  # stored in the private directory

    guest = {"X-Order-Token": order.guest_order_token}
    listing = client.get(f"/api/v1/orders/{order.id}/documents", headers=guest)
    assert [d["id"] for d in listing.json()] == [doc["id"]]
    assert "storage_name" not in listing.json()[0]

    link = client.post(f"/api/v1/orders/{order.id}/documents/{doc['id']}/link", headers=guest).json()
    got = client.get(link["url"].replace(settings.BACKEND_URL.rstrip("/"), ""))
    assert got.status_code == 200 and got.content == PDF
    assert got.headers["cache-control"] == "private, no-store"


def test_strangers_and_bad_links_get_nothing(client, db_session, sku):
    order, admin = _setup(client, db_session, sku)
    doc = _upload(client, admin, order.id).json()

    assert client.get(f"/api/v1/orders/{order.id}/documents").status_code == 404
    assert client.get(f"/api/v1/orders/{order.id}/documents", headers={"X-Order-Token": "wrong"}).status_code == 404
    assert client.post(f"/api/v1/orders/{order.id}/documents/{doc['id']}/link").status_code == 404
    assert client.get("/api/v1/documents/download?token=garbage").status_code == 404
    # a login token is not a document link
    from app.core.security import create_access_token
    assert client.get(f"/api/v1/documents/download?token={create_access_token('1')}").status_code == 404
    assert client.post(f"/api/v1/admin/orders/{order.id}/documents", files={"file": ("a.pdf", PDF, "application/pdf")}, data={"doc_type": "invoice"}).status_code == 401


def test_only_real_pdf_or_images_are_accepted_and_void_hides_document(client, db_session, sku):
    order, admin = _setup(client, db_session, sku)
    assert _upload(client, admin, order.id, content=b"<script>alert(1)</script>").status_code == 400
    assert _upload(client, admin, order.id, ctype="text/html").status_code == 400
    assert _upload(client, admin, order.id, doc_type="love-letter").status_code == 400

    doc = _upload(client, admin, order.id).json()
    guest = {"X-Order-Token": order.guest_order_token}
    link = client.post(f"/api/v1/orders/{order.id}/documents/{doc['id']}/link", headers=guest).json()["url"]
    assert client.post(f"/api/v1/admin/orders/{order.id}/documents/{doc['id']}/void", headers=admin).json()["status"] == "void"
    assert client.get(f"/api/v1/orders/{order.id}/documents", headers=guest).json() == []
    assert client.get(link.replace(settings.BACKEND_URL.rstrip("/"), "")).status_code == 404


def test_storage_name_cannot_escape_directory():
    with pytest.raises(ValueError):
        documents.path_of("../secret.txt")
