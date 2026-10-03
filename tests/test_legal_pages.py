"""The privacy and terms pages are editable page-section keys and are in the sitemap."""

from app.models.enums import UserRole
from conftest import login, make_admin


def _admin(client, db_session):
    make_admin(db_session, "content@example.com", UserRole.MARKETING_MANAGER)
    return login(client, "content@example.com")


def test_privacy_and_terms_are_valid_page_keys(client, db_session):
    headers = _admin(client, db_session)
    for key in ("privacy", "terms"):
        r = client.post("/api/v1/admin/page-sections", headers=headers, json={"page": key, "title": f"{key} title", "body": "text"})
        assert r.status_code in (200, 201), (key, r.text)
        listed = client.get(f"/api/v1/page-sections?page={key}").json()
        assert [s["title"] for s in listed] == [f"{key} title"]


def test_unknown_page_key_is_still_rejected(client):
    assert client.get("/api/v1/page-sections?page=nonsense").status_code == 422


def test_public_page_sections_empty_until_an_admin_writes_some(client):
    # The storefront falls back to its built-in default text in this case.
    assert client.get("/api/v1/page-sections?page=privacy").json() == []


def test_sitemap_lists_privacy_and_terms(client):
    body = client.get("/sitemap.xml").text
    assert "/privacy</loc>" in body and "/terms</loc>" in body
