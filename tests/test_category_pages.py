"""Category page content: admin editing, per-language overrides and the public page (PRD ТЗ№2 §10)."""

from app.models.category import Category
from app.models.enums import UserRole
from conftest import login, make_admin

BASE = "/api/v1/admin/categories"


def _admin(client, db_session):
    make_admin(db_session, "pm@example.com", UserRole.PRODUCT_MANAGER)
    return login(client, "pm@example.com")


def test_admin_sets_page_content_and_the_public_page_shows_it(client, db_session):
    h = _admin(client, db_session)
    parent = client.post(f"{BASE}/", json={"name": "Containers", "slug": "containers", "description": "All boxes", "seo_content": "Long text", "image_url": "https://img.example/c.jpg"}, headers=h)
    assert parent.status_code == 201, parent.text
    child = client.post(f"{BASE}/", json={"name": "Round", "slug": "round", "parent_id": parent.json()["id"]}, headers=h)
    assert child.status_code == 201, child.text

    page = client.get("/api/v1/categories/containers").json()
    assert page["name"] == "Containers" and page["description"] == "All boxes" and page["seo_content"] == "Long text"
    assert page["image_url"] == "https://img.example/c.jpg" and page["parent"] is None
    assert [c["slug"] for c in page["children"]] == ["round"]
    assert client.get("/api/v1/categories/round").json()["parent"]["slug"] == "containers"
    assert client.get("/api/v1/categories/nope").status_code == 404


def test_translations_override_name_description_and_seo_text(client, db_session):
    h = _admin(client, db_session)
    cid = client.post(f"{BASE}/", json={"name": "Containers", "slug": "containers", "description": "EN text"}, headers=h).json()["id"]
    r = client.put(f"{BASE}/{cid}/translations/ru", json={"name": "Контейнеры", "description": "Описание", "seo_content": "SEO ru"}, headers=h)
    assert r.status_code == 200, r.text
    listed = client.get(f"{BASE}/{cid}/translations", headers=h).json()
    assert [(t["locale"], t["description"]) for t in listed] == [("ru", "Описание")]

    ru = client.get("/api/v1/categories/containers", params={"lang": "ru"}).json()
    assert (ru["name"], ru["description"], ru["seo_content"]) == ("Контейнеры", "Описание", "SEO ru")
    uz = client.get("/api/v1/categories/containers", params={"lang": "uz"}).json()  # no uz override: base text
    assert (uz["name"], uz["description"]) == ("Containers", "EN text")


def test_image_url_must_be_http(client, db_session):
    h = _admin(client, db_session)
    bad = client.post(f"{BASE}/", json={"name": "X", "slug": "x", "image_url": "javascript:alert(1)"}, headers=h)
    assert bad.status_code == 422
    ok = client.post(f"{BASE}/", json={"name": "Y", "slug": "y", "image_url": ""}, headers=h)
    assert ok.status_code == 201 and db_session.query(Category).filter_by(slug="y").one().image_url is None


def test_sitemap_lists_category_pages_and_the_new_info_pages(client, db_session):
    from app.models.category import Category

    db_session.add(Category(name="Lids", slug="lids"))
    db_session.commit()
    body = client.get("/sitemap.xml").text
    for path in ("/shop/lids", "/manufacturing", "/quality"):
        assert path in body
