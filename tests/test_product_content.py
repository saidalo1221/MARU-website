"""PRD ТЗ№1 §29-30: SEO fields and content blocks on a product, also per language."""

from app.models.enums import UserRole
from conftest import login, make_admin

API = "/api/v1/admin/products"


def test_content_fields_roundtrip_with_language_overrides(client, db_session, sku):
    make_admin(db_session, "pm@example.com", UserRole.PRODUCT_MANAGER)
    h = login(client, "pm@example.com")
    pid, slug = sku.variant.product_id, sku.variant.product.slug
    content = {
        "seo_title": "Buy MARU 1000 ml food container", "meta_description": "Airtight PP container, 1 L.",
        "advantages": "Airtight lid\nMicrowave safe", "usage_scenarios": "Meal prep\nLunch boxes",
        "instructions": "Hand wash or dishwasher.", "material_info": "Food-grade polypropylene (PP 5).",
    }
    assert client.patch(f"{API}/{pid}", json=content, headers=h).status_code == 200
    page = client.get(f"/api/v1/products/{slug}").json()
    assert {k: page[k] for k in content} == content

    ru = {"name": "Контейнер", **{k: v + " (ru)" for k, v in content.items() if k in ("seo_title", "advantages")}}
    assert client.put(f"{API}/{pid}/translations/ru", json=ru, headers=h).status_code == 200
    page_ru = client.get(f"/api/v1/products/{slug}?lang=ru").json()
    assert page_ru["seo_title"].endswith("(ru)") and page_ru["advantages"].endswith("(ru)")
    assert page_ru["instructions"] == content["instructions"]            # not translated: falls back to the base text
    assert client.get(f"/api/v1/products/{slug}?lang=en").json()["seo_title"] == content["seo_title"]
    assert client.patch(f"{API}/{pid}", json={"meta_description": "x" * 400}, headers=h).status_code == 422
