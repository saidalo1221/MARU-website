"""Admin media uploads: product-gallery video (mp4/webm, 25MB cap) and images
(5MB cap). Files are written to a temp dir, never the real static/uploads."""

import pytest

from app.models.enums import UserRole
from conftest import login, make_admin, register


@pytest.fixture()
def upload_dir(tmp_path, monkeypatch):
    import app.routers.admin_uploads as uploads

    monkeypatch.setattr(uploads, "UPLOAD_DIR", tmp_path)
    return tmp_path


@pytest.fixture()
def pm_headers(client, db_session):
    make_admin(db_session, "pm-upload@example.com", UserRole.PRODUCT_MANAGER)
    return login(client, "pm-upload@example.com")


MP4 = b"\x00\x00\x00\x18ftypmp42"
WEBM = b"\x1a\x45\xdf\xa3"
PNG = b"\x89PNG\r\n\x1a\n"


def _post(client, headers, path, name, data, content_type):
    return client.post(f"/api/v1/admin/uploads/{path}", headers=headers, files={"file": (name, data, content_type)})


@pytest.mark.parametrize("name,content_type,ext", [("clip.mp4", "video/mp4", ".mp4"), ("clip.webm", "video/webm", ".webm")])
def test_video_upload_accepts_mp4_and_webm(client, pm_headers, upload_dir, name, content_type, ext):
    data = MP4 if content_type == "video/mp4" else WEBM
    r = _post(client, pm_headers, "video", name, data + b"0" * 64, content_type)
    assert r.status_code == 200, r.text
    url = r.json()["url"]
    assert url.endswith(ext)
    assert (upload_dir / url.rsplit("/", 1)[1]).exists()


@pytest.mark.parametrize("content_type", ["video/x-msvideo", "video/quicktime", "text/plain", "image/png"])
def test_video_upload_rejects_other_types(client, pm_headers, upload_dir, content_type):
    r = _post(client, pm_headers, "video", "clip.bin", b"data", content_type)
    assert r.status_code == 400
    assert list(upload_dir.iterdir()) == []


def test_video_upload_enforces_25mb_cap(client, pm_headers, upload_dir):
    import app.routers.admin_uploads as uploads

    at_limit = MP4 + b"0" * (uploads.MAX_VIDEO_BYTES - len(MP4))
    assert _post(client, pm_headers, "video", "ok.mp4", at_limit, "video/mp4").status_code == 200

    r = _post(client, pm_headers, "video", "big.mp4", at_limit + b"0", "video/mp4")
    assert r.status_code == 400
    assert "25MB" in r.json()["detail"]
    assert len(list(upload_dir.iterdir())) == 1  # only the at-limit file was stored


def test_image_upload_enforces_5mb_cap_and_type(client, pm_headers, upload_dir):
    assert _post(client, pm_headers, "image", "a.png", PNG + b"0" * 10, "image/png").status_code == 200
    assert _post(client, pm_headers, "image", "a.svg", b"<svg/>", "image/svg+xml").status_code == 400
    assert _post(client, pm_headers, "image", "big.png", PNG + b"0" * (5 * 1024 * 1024), "image/png").status_code == 400


def test_uploads_require_admin_role(client, upload_dir):
    customer = register(client, "buyer-upload@example.com")
    assert _post(client, customer, "video", "clip.mp4", b"x", "video/mp4").status_code == 403
    assert _post(client, None, "video", "clip.mp4", b"x", "video/mp4").status_code in (401, 403)
    assert list(upload_dir.iterdir()) == []


@pytest.mark.parametrize(
    "path,content_type,data",
    [
        ("image", "image/png", b"<script>alert(1)</script>"),
        ("image", "image/jpeg", PNG + b"0" * 10),
        ("image", "image/gif", b"not a gif"),
        ("video", "video/mp4", b"<html>x</html>"),
        ("video", "video/webm", MP4 + b"0" * 10),
    ],
)
def test_upload_rejects_content_that_does_not_match_declared_type(client, pm_headers, upload_dir, path, content_type, data):
    r = _post(client, pm_headers, path, "x.bin", data, content_type)
    assert r.status_code == 400
    assert "does not match" in r.json()["detail"]
    assert list(upload_dir.iterdir()) == []


@pytest.mark.parametrize(
    "content_type,data",
    [
        ("image/jpeg", b"\xff\xd8\xff\xe0" + b"0" * 8),
        ("image/gif", b"GIF89a" + b"0" * 8),
        ("image/webp", b"RIFF\x00\x00\x00\x00WEBP" + b"0" * 8),
    ],
)
def test_image_upload_accepts_real_signatures(client, pm_headers, upload_dir, content_type, data):
    assert _post(client, pm_headers, "image", "x", data, content_type).status_code == 200
