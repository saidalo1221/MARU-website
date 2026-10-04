"""PRD ТЗ№1 §32: reviews can carry photos; admins approve, hide or delete them."""

import io

from PIL import Image

from app.config import settings
from app.models.enums import OrderStatus, UserRole
from app.models.user import User
from app.routers import admin_uploads
from app.schemas.order import CheckoutRequest
from app.services.order_service import create_order, set_order_status
from conftest import CHECKOUT_PAYLOAD, login, make_admin, register
from test_orders_reservation import _cart_with


def _png():
    buf = io.BytesIO()
    Image.new("RGB", (40, 30), "blue").save(buf, "PNG")
    return buf.getvalue()


def _buyer(client, db_session, sku, tmp_path, monkeypatch):
    monkeypatch.setattr(admin_uploads, "UPLOAD_DIR", tmp_path)
    register(client, "buyer@example.com")
    user = db_session.query(User).filter_by(email="buyer@example.com").one()
    order = create_order(db_session, _cart_with(db_session, sku, 1), CheckoutRequest(**CHECKOUT_PAYLOAD), user)
    db_session.commit()
    set_order_status(db_session, order, OrderStatus.PAID, None)
    return login(client, "buyer@example.com")


def test_review_with_photos_then_moderation(client, db_session, sku, tmp_path, monkeypatch):
    h = _buyer(client, db_session, sku, tmp_path, monkeypatch)
    slug = sku.variant.product.slug
    up = client.post("/api/v1/reviews/images", files={"file": ("p.png", _png(), "image/png")}, headers=h)
    assert up.status_code == 201, up.text
    url = up.json()["url"]
    assert url.startswith(f"{settings.BACKEND_URL.rstrip('/')}/static/uploads/rv-")

    r = client.post(f"/api/v1/products/{slug}/reviews", json={"rating": 5, "content": "Great", "image_urls": [url]}, headers=h)
    assert r.status_code == 201 and r.json()["image_urls"] == [url]
    assert client.get(f"/api/v1/products/{slug}/reviews").json()["reviews"] == []  # still pending

    make_admin(db_session, "mk@example.com", UserRole.MARKETING_MANAGER)
    ah = login(client, "mk@example.com")
    rid = r.json()["id"]
    assert client.patch(f"/api/v1/admin/reviews/{rid}", json={"status": "approved"}, headers=ah).status_code == 200
    shown = client.get(f"/api/v1/products/{slug}/reviews").json()["reviews"]
    assert shown[0]["image_urls"] == [url]
    assert client.patch(f"/api/v1/admin/reviews/{rid}", json={"status": "rejected"}, headers=ah).status_code == 200
    assert client.get(f"/api/v1/products/{slug}/reviews").json()["reviews"] == []
    assert client.delete(f"/api/v1/admin/reviews/{rid}", headers=ah).status_code == 204
    assert client.delete(f"/api/v1/admin/reviews/{rid}", headers=ah).status_code == 404


def test_only_our_own_uploads_and_real_images_are_accepted(client, db_session, sku, tmp_path, monkeypatch):
    h = _buyer(client, db_session, sku, tmp_path, monkeypatch)
    slug = sku.variant.product.slug
    for bad in ("https://evil.example/x.png", f"{settings.BACKEND_URL}/static/uploads/rv-../secret.png", f"{settings.BACKEND_URL}/static/uploads/rv-missing.png"):
        r = client.post(f"/api/v1/products/{slug}/reviews", json={"rating": 4, "image_urls": [bad]}, headers=h)
        assert r.status_code == 400, bad
    too_many = [f"{settings.BACKEND_URL}/static/uploads/rv-{i}.png" for i in range(4)]
    assert client.post(f"/api/v1/products/{slug}/reviews", json={"rating": 4, "image_urls": too_many}, headers=h).status_code == 422

    assert client.post("/api/v1/reviews/images", files={"file": ("p.png", b"not an image", "image/png")}, headers=h).status_code == 400
    assert client.post("/api/v1/reviews/images", files={"file": ("p.gif", _png(), "image/gif")}, headers=h).status_code == 400
    assert client.post("/api/v1/reviews/images", files={"file": ("p.png", _png(), "image/png")}).status_code == 401
