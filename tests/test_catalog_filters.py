"""Server-side catalog filters, sorting and paging (PRD ТЗ№3 §44, §51-53)."""

from decimal import Decimal

from app.models.category import Category
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.review import Review, ReviewStatus
from app.models.sku import SKU
from app.models.user import User
from conftest import register

URL = "/api/v1/products/"


def _product(db, category, slug, volume, color, price, stock, warehouse, special=None):
    p = Product(category_id=category.id, name=slug, slug=slug, volume_ml=volume)
    db.add(p)
    db.flush()
    v = ProductVariant(product_id=p.id, name=color, color=color)
    db.add(v)
    db.flush()
    s = SKU(variant_id=v.id, sku_code=f"SKU-{slug}", retail_price=Decimal(price), special_price=special, currency="USD")
    db.add(s)
    db.flush()
    db.add(Inventory(sku_id=s.id, warehouse_id=warehouse.id, stock=stock, reserved=0))
    return p


def _catalog(db_session, warehouse):
    cat_a = Category(name="A", slug="cat-a")
    cat_b = Category(name="B", slug="cat-b")
    db_session.add_all([cat_a, cat_b])
    db_session.flush()
    prods = {
        "cheap": _product(db_session, cat_a, "cheap", 350, "clear", "3", 10, warehouse),
        "mid": _product(db_session, cat_a, "mid", 800, "white", "8", 0, warehouse),
        "pricey": _product(db_session, cat_b, "pricey", 1000, "Clear", "20", 5, warehouse),
    }
    db_session.commit()
    return cat_a, cat_b, prods


def _slugs(r):
    assert r.status_code == 200, r.text
    return [p["slug"] for p in r.json()]


def test_filters(client, db_session, warehouse):
    cat_a, cat_b, _ = _catalog(db_session, warehouse)
    assert _slugs(client.get(URL)) == ["cheap", "mid", "pricey"]
    assert _slugs(client.get(URL, params={"category_id": cat_a.id})) == ["cheap", "mid"]
    assert _slugs(client.get(URL, params={"capacity": 1000})) == ["pricey"]
    assert _slugs(client.get(URL, params={"color": "clear"})) == ["cheap", "pricey"]  # case-insensitive
    assert _slugs(client.get(URL, params={"material": "polypropylene"})) == ["cheap", "mid", "pricey"]
    assert _slugs(client.get(URL, params={"availability": "in_stock"})) == ["cheap", "pricey"]
    assert _slugs(client.get(URL, params={"price_min": 5, "price_max": 10})) == ["mid"]
    assert _slugs(client.get(URL, params={"price_min": 5})) == ["mid", "pricey"]


def test_sorting_whitelist(client, db_session, warehouse):
    _catalog(db_session, warehouse)
    assert _slugs(client.get(URL, params={"sort": "price_asc"})) == ["cheap", "mid", "pricey"]
    assert _slugs(client.get(URL, params={"sort": "price_desc"})) == ["pricey", "mid", "cheap"]
    assert _slugs(client.get(URL, params={"sort": "newest"})) == ["pricey", "mid", "cheap"]
    assert client.get(URL, params={"sort": "id; DROP TABLE products"}).status_code == 400


def test_sale_price_is_used_for_price_sort_and_filter(client, db_session, warehouse):
    cat_a, _, prods = _catalog(db_session, warehouse)
    pricey_sku = prods["pricey"].variants[0].skus[0]
    pricey_sku.special_price = Decimal("1")
    db_session.commit()
    assert _slugs(client.get(URL, params={"sort": "price_asc"}))[0] == "pricey"
    assert _slugs(client.get(URL, params={"price_max": 2})) == ["pricey"]


def test_paging_and_total_header(client, db_session, warehouse):
    _catalog(db_session, warehouse)
    r = client.get(URL, params={"limit": 2, "page": 1, "sort": "price_asc"})
    assert [p["slug"] for p in r.json()] == ["cheap", "mid"]
    assert r.headers["X-Total-Count"] == "3"
    r = client.get(URL, params={"limit": 2, "page": 2, "sort": "price_asc"})
    assert [p["slug"] for p in r.json()] == ["pricey"]
    assert client.get(URL, params={"limit": 101}).status_code == 422  # max page size is 100
    assert client.get(URL, params={"page": 0}).status_code == 422
    unpaged = client.get(URL)
    assert len(unpaged.json()) == 3 and unpaged.headers["X-Total-Count"] == "3"


def test_rating_is_returned_and_sortable(client, db_session, warehouse):
    _, _, prods = _catalog(db_session, warehouse)
    register(client, "rev@example.com")
    uid = db_session.query(User).filter_by(email="rev@example.com").one().id
    db_session.add_all(
        [
            Review(user_id=uid, product_id=prods["mid"].id, rating=5, status=ReviewStatus.APPROVED),
            Review(user_id=uid, product_id=prods["cheap"].id, rating=2, status=ReviewStatus.APPROVED),
            Review(user_id=uid, product_id=prods["pricey"].id, rating=1, status=ReviewStatus.PENDING),  # not counted
        ]
    )
    db_session.commit()

    r = client.get(URL, params={"sort": "rating"})
    assert [p["slug"] for p in r.json()][:2] == ["mid", "cheap"]
    by_slug = {p["slug"]: p for p in r.json()}
    assert by_slug["mid"]["rating_average"] == 5.0 and by_slug["mid"]["rating_count"] == 1
    assert by_slug["cheap"]["rating_average"] == 2.0 and by_slug["cheap"]["rating_count"] == 1
    assert by_slug["pricey"]["rating_average"] is None and by_slug["pricey"]["rating_count"] == 0
    detail = client.get(f"{URL}mid").json()
    assert detail["rating_average"] == 5.0


def test_featured_reviews_expose_only_first_name_and_approved_text(client, db_session, warehouse):
    _, _, prods = _catalog(db_session, warehouse)
    register(client, "fan@example.com")
    user = db_session.query(User).filter_by(email="fan@example.com").one()
    user.first_name, user.last_name = "Dilnoza", "Secret"
    other = User(email="other@example.com", password_hash="x", first_name="Bek")
    db_session.add(other)
    db_session.flush()
    db_session.add_all(
        [
            Review(user_id=user.id, product_id=prods["mid"].id, rating=5, content="Great box", status=ReviewStatus.APPROVED),
            Review(user_id=user.id, product_id=prods["cheap"].id, rating=4, content="Pending text", status=ReviewStatus.PENDING),
            Review(user_id=other.id, product_id=prods["mid"].id, rating=3, content=None, status=ReviewStatus.APPROVED),
        ]
    )
    db_session.commit()

    r = client.get("/api/v1/reviews/featured")
    assert r.status_code == 200, r.text
    assert r.json() == [
        {"id": r.json()[0]["id"], "rating": 5, "content": "Great box", "author": "Dilnoza", "product_name": "mid", "product_slug": "mid"}
    ]
    assert "Secret" not in r.text and "@" not in r.text
    assert client.get("/api/v1/reviews/featured", params={"limit": 50}).status_code == 422
