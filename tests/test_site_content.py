from app.models.enums import UserRole
from conftest import login, make_admin


def _admin(client, db_session):
    make_admin(db_session, "mkt2@example.com", UserRole.MARKETING_MANAGER)
    return login(client, "mkt2@example.com")


def test_text_overrides_roundtrip(client, db_session):
    h = _admin(client, db_session)
    assert client.get("/api/v1/content-overrides", params={"lang": "en"}).json() == {}

    r = client.put("/api/v1/admin/content-overrides", json={"items": [
        {"key": "home.title", "locale": "en", "value": "New headline"},
        {"key": "home.cta", "locale": "ru", "value": "Купить"},
    ]}, headers=h)
    assert r.status_code == 200, r.text
    assert client.get("/api/v1/content-overrides", params={"lang": "en"}).json() == {"home.title": "New headline"}

    # update, then an empty value removes it (built-in text shows again)
    client.put("/api/v1/admin/content-overrides", json={"items": [{"key": "home.title", "locale": "en", "value": "Newer"}]}, headers=h)
    assert client.get("/api/v1/content-overrides", params={"lang": "en"}).json()["home.title"] == "Newer"
    client.put("/api/v1/admin/content-overrides", json={"items": [{"key": "home.title", "locale": "en", "value": "  "}]}, headers=h)
    assert client.get("/api/v1/content-overrides", params={"lang": "en"}).json() == {}


def test_content_editing_needs_staff_and_validates(client, db_session):
    assert client.put("/api/v1/admin/content-overrides", json={"items": []}).status_code in (401, 403)
    h = _admin(client, db_session)
    bad = client.put("/api/v1/admin/content-overrides", json={"items": [{"key": "bad key!", "locale": "en", "value": "x"}]}, headers=h)
    assert bad.status_code == 422
    assert client.get("/api/v1/content-overrides", params={"lang": "de"}).status_code == 422


def test_seo_tags_roundtrip(client, db_session):
    h = _admin(client, db_session)
    body = {"path": "/shop", "locale": "en", "title": "Buy containers", "description": "Wholesale and retail", "image_url": "", "noindex": False}
    assert client.put("/api/v1/admin/seo-meta", json=body, headers=h).status_code == 200
    assert client.get("/api/v1/seo-meta", params={"lang": "en"}).json() == {
        "/shop": {"title": "Buy containers", "description": "Wholesale and retail", "image": None, "noindex": False}
    }
    assert client.get("/api/v1/seo-meta", params={"lang": "ru"}).json() == {}

    # clearing every field removes the row
    clear = {"path": "/shop", "locale": "en", "title": "", "description": "", "image_url": "", "noindex": False}
    client.put("/api/v1/admin/seo-meta", json=clear, headers=h)
    assert client.get("/api/v1/seo-meta", params={"lang": "en"}).json() == {}

    assert client.put("/api/v1/admin/seo-meta", json={**body, "path": "shop"}, headers=h).status_code == 422
