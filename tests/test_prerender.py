"""PRD ТЗ№3 §85 / ТЗ№2 §62: crawlers and link previews get a complete HTML page."""

import json
import re

from app.models.blog_post import BlogPost
from app.models.category import Category
from app.models.enums import UserRole
from conftest import login, make_admin


def _ld(page):
    return json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S).group(1))


def test_product_page_has_meta_open_graph_and_structured_data(client, db_session, sku):
    make_admin(db_session, "pm@example.com", UserRole.PRODUCT_MANAGER)
    h = login(client, "pm@example.com")
    client.patch(f"/api/v1/admin/products/{sku.variant.product_id}", json={"seo_title": "Buy <MARU> box", "meta_description": "Airtight & strong", "advantages": "Airtight\nStrong"}, headers=h)
    r = client.get(f"/prerender/products/{sku.variant.product.slug}")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/html")
    page = r.text
    assert "<title>Buy &lt;MARU&gt; box | MARU</title>" in page                      # escaped
    assert 'name="description" content="Airtight &amp; strong"' in page
    assert 'rel="canonical" href="http://localhost:5173/products/food-container"' in page
    assert 'property="og:title"' in page and "<h1>Food Container</h1>" in page and "<li>Airtight</li>" in page
    ld = _ld(page)
    assert ld["@type"] == "Product" and ld["offers"]["priceCurrency"] == "USD" and ld["offers"]["lowPrice"] == 10.0
    assert ld["offers"]["availability"].endswith("InStock")


def test_category_blog_home_and_unknown(client, db_session, sku):
    db_session.add(Category(name="Lunch Boxes", slug="lunch-boxes", description="Boxes for lunch"))
    from datetime import datetime
    db_session.add(BlogPost(category_id=1, slug="hello", title="Hello </script>", content="Body", is_published=True, published_at=datetime(2026, 1, 1)))
    db_session.commit()
    cat = client.get("/prerender/shop/lunch-boxes").text
    assert "<h1>Lunch Boxes</h1>" in cat and "Boxes for lunch" in cat
    post = client.get("/prerender/blog/hello").text
    assert "Hello &lt;/script&gt;" in post and _ld(post)["@type"] == "BlogPosting"
    assert "</script></script>" not in post                                         # JSON-LD cannot be broken out of
    assert 'rel="canonical" href="http://localhost:5173"' in client.get("/prerender/").text
    for path in ("/prerender/products/nope", "/prerender/shop/nope", "/prerender/blog/nope"):
        assert client.get(path).status_code == 404


def test_unpublished_posts_and_inactive_products_are_not_exposed(client, db_session, sku):
    from datetime import datetime
    db_session.add(BlogPost(category_id=1, slug="draft", title="Draft", content="x", is_published=False, published_at=datetime(2026, 1, 1)))
    sku.is_active = False
    db_session.commit()
    assert client.get("/prerender/blog/draft").status_code == 404
    assert client.get(f"/prerender/products/{sku.variant.product.slug}").status_code == 404
    assert "/prerender" not in client.get("/openapi.json").text if client.get("/openapi.json").status_code == 200 else True
