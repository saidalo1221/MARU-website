"""PRD ТЗ№1 §46-47: search, autocomplete and filter facets run in the database."""

from app.models.category import Category
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_translation import ProductTranslation
from app.models.product_variant import ProductVariant
from app.models.sku import SKU


def _add(db_session, warehouse, name, slug, volume, code, color="clear", category=None, shape=None, price=5):
    category = category or db_session.query(Category).first()
    product = Product(category_id=category.id, name=name, slug=slug, volume_ml=volume, shape=shape)
    db_session.add(product)
    db_session.flush()
    variant = ProductVariant(product_id=product.id, name=color, color=color)
    db_session.add(variant)
    db_session.flush()
    sku = SKU(variant_id=variant.id, sku_code=code, retail_price=price, currency="USD")
    db_session.add(sku)
    db_session.flush()
    db_session.add(Inventory(sku_id=sku.id, warehouse_id=warehouse.id, stock=10, reserved=0))
    db_session.commit()
    return product


def _catalog(db_session, warehouse):
    db_session.add(Category(name="Food Containers", slug="food-containers"))
    db_session.add(Category(name="Lunch Boxes", slug="lunch-boxes"))
    db_session.commit()
    cats = {c.slug: c for c in db_session.query(Category)}
    a = _add(db_session, warehouse, "MARU Round Container", "round", 350, "SKU-350-TR", category=cats["food-containers"], shape="round")
    b = _add(db_session, warehouse, "MARU Square Container", "square", 1000, "SKU-1000-WH", color="white", category=cats["food-containers"], shape="square")
    c = _add(db_session, warehouse, "Bento Lunch Box", "bento", 800, "BENTO-800", category=cats["lunch-boxes"])
    return cats, a, b, c


def _slugs(r):
    return [p["slug"] for p in r.json()]


def test_search_by_name_sku_category_shape_and_volume(client, db_session, warehouse):
    _catalog(db_session, warehouse)
    S = "/api/v1/products/"
    assert set(_slugs(client.get(S, params={"q": "container"}))) == {"round", "square"}
    assert _slugs(client.get(S, params={"q": "bento"})) == ["bento"]
    assert _slugs(client.get(S, params={"q": "sku-1000-wh"})) == ["square"]          # SKU code, any case
    assert set(_slugs(client.get(S, params={"q": "lunch"}))) == {"bento"}            # category name
    assert _slugs(client.get(S, params={"q": "round"})) == ["round"]                 # shape / name
    assert _slugs(client.get(S, params={"q": "1000ml"})) == ["square"]               # volume
    assert _slugs(client.get(S, params={"q": "maru square"})) == ["square"]          # every word must match
    assert client.get(S, params={"q": "zzzzzz"}).json() == []
    r = client.get(S, params={"q": "container", "limit": 1})
    assert r.headers["x-total-count"] == "2" and len(r.json()) == 1


def test_ranking_exact_sku_then_prefix_then_contains(client, db_session, warehouse):
    cats, *_ = _catalog(db_session, warehouse)
    _add(db_session, warehouse, "Premium Bento Set", "premium-bento", 470, "PB-470", category=cats["lunch-boxes"])
    _add(db_session, warehouse, "Cap", "cap", 350, "bento", category=cats["lunch-boxes"])  # SKU code equals the query
    order = _slugs(client.get("/api/v1/products/", params={"q": "bento"}))
    assert order[0] == "cap" and order.index("bento") < order.index("premium-bento")


def test_typos_are_tolerated_when_nothing_matches_exactly(client, db_session, warehouse):
    _catalog(db_session, warehouse)
    S = "/api/v1/products/"
    assert _slugs(client.get(S, params={"q": "contaner"})) and set(_slugs(client.get(S, params={"q": "contaner"}))) == {"round", "square"}
    assert _slugs(client.get(S, params={"q": "bnto"})) == ["bento"]
    assert client.get(S, params={"q": "qwertyuiop"}).json() == []


def test_translated_names_are_searchable_in_that_language(client, db_session, warehouse):
    _cats, a, *_ = _catalog(db_session, warehouse)
    db_session.add(ProductTranslation(product_id=a.id, locale="ru", name="Круглый контейнер"))
    db_session.commit()
    assert _slugs(client.get("/api/v1/products/", params={"q": "круглый", "lang": "ru"})) == ["round"]
    assert client.get("/api/v1/products/", params={"q": "круглый", "lang": "en"}).json() == []


def test_like_wildcards_in_the_query_are_not_wildcards(client, db_session, warehouse):
    _catalog(db_session, warehouse)
    assert client.get("/api/v1/products/", params={"q": "%%%"}).json() == []
    assert client.get("/api/v1/products/", params={"q": "_____"}).json() == []


def test_suggest_returns_light_hits_and_categories(client, db_session, warehouse):
    _catalog(db_session, warehouse)
    body = client.get("/api/v1/products/suggest", params={"q": "lunch"}).json()
    assert [p["slug"] for p in body["products"]] == ["bento"] and set(body["products"][0]) == {"id", "name", "slug", "volume_ml", "category_id"}
    assert [c["slug"] for c in body["categories"]] == ["lunch-boxes"]


def test_facets_and_category_ids_filter(client, db_session, warehouse):
    cats, *_ = _catalog(db_session, warehouse)
    f = client.get("/api/v1/products/facets").json()
    assert f["capacities"] == [350, 800, 1000] and f["colors"] == ["clear", "white"] and f["materials"] == ["polypropylene"]
    assert f["category_ids"] == sorted(c.id for c in cats.values())
    only = client.get("/api/v1/products/facets", params={"category_ids": str(cats["lunch-boxes"].id)}).json()
    assert only["capacities"] == [800] and only["category_ids"] == [cats["lunch-boxes"].id]

    ids = f"{cats['lunch-boxes'].id},{cats['food-containers'].id}"
    assert len(client.get("/api/v1/products/", params={"category_ids": ids}).json()) == 3
    assert [p["slug"] for p in client.get("/api/v1/products/", params={"category_ids": str(cats["lunch-boxes"].id)}).json()] == ["bento"]
    assert client.get("/api/v1/products/", params={"category_ids": "x"}).status_code == 400


def test_facets_refresh_after_a_product_changes(client, db_session, warehouse):
    cats, *_ = _catalog(db_session, warehouse)
    assert client.get("/api/v1/products/facets").json()["capacities"] == [350, 800, 1000]
    _add(db_session, warehouse, "Big", "big", 1900, "BIG-1900", category=cats["food-containers"])
    assert 1900 in client.get("/api/v1/products/facets").json()["capacities"]


def test_search_combines_with_sort_filters_and_paging(client, db_session, warehouse):
    cats, *_ = _catalog(db_session, warehouse)
    _add(db_session, warehouse, "MARU Cheap Container", "cheap", 470, "CH-470", category=cats["food-containers"], price=1)
    _add(db_session, warehouse, "MARU Pricey Container", "pricey", 1900, "PR-1900", category=cats["food-containers"], price=50)
    P = "/api/v1/products/"
    asc = _slugs(client.get(P, params={"q": "container", "sort": "price_asc"}))
    assert asc[0] == "cheap" and asc[-1] == "pricey" and set(asc) == {"round", "square", "cheap", "pricey"}
    assert _slugs(client.get(P, params={"q": "container", "sort": "price_desc", "limit": 1})) == ["pricey"]
    assert set(_slugs(client.get(P, params={"q": "container", "price_min": 4, "price_max": 10}))) == {"round", "square"}
    r = client.get(P, params={"q": "container", "limit": 2, "page": 2, "sort": "price_asc"})
    assert r.headers["x-total-count"] == "4" and len(r.json()) == 2
    # typos still combine with a filter and sort
    assert _slugs(client.get(P, params={"q": "contaner", "sort": "price_desc", "capacity": 1900})) == ["pricey"]
    # out of stock products drop out with availability=in_stock
    inv = db_session.query(Inventory).filter(Inventory.sku_id == db_session.query(SKU).filter_by(sku_code="CH-470").one().id).one()
    inv.stock = 0
    db_session.commit()
    assert "cheap" not in _slugs(client.get(P, params={"q": "container", "availability": "in_stock"}))
    assert "cheap" in _slugs(client.get(P, params={"q": "container"}))
