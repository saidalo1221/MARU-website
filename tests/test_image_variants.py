"""PRD ТЗ№3 §86: uploaded images get WebP copies at several widths."""

import io

import pytest
from PIL import Image

from app.models.enums import UserRole
from app.routers import admin_uploads
from conftest import login, make_admin


def test_upload_writes_webp_variants_without_enlarging(client, db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(admin_uploads, "UPLOAD_DIR", tmp_path)
    make_admin(db_session, "pm@example.com", UserRole.PRODUCT_MANAGER)
    h = login(client, "pm@example.com")
    buf = io.BytesIO()
    Image.new("RGB", (1000, 500), "red").save(buf, "PNG")

    r = client.post("/api/v1/admin/uploads/image", files={"file": ("a.png", buf.getvalue(), "image/png")}, headers=h)
    assert r.status_code == 200, r.text
    name = r.json()["url"].rsplit("/", 1)[1]
    assert name.startswith("img-") and (tmp_path / name).exists()
    base = name.rsplit(".", 1)[0]

    widths = {w: Image.open(tmp_path / f"{base}-{w}.webp").size[0] for w in (320, 800, 1600)}
    assert widths == {320: 320, 800: 800, 1600: 1000}  # the 1600 copy is not blown up past the original

    from PIL import features

    if features.check("avif"):  # Pillow 11.3+; older builds skip AVIF and the page falls back to WebP
        avif = {w: Image.open(tmp_path / f"{base}-{w}.avif").size[0] for w in (320, 800, 1600)}
        assert avif == widths
    else:
        assert not list(tmp_path.glob("*.avif"))
