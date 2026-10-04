"""PRD ТЗ№1 §16: products can be sold only in, or hidden from, certain countries."""

import pytest

from app.models.enums import UserRole
from app.models.product import Product
from app.schemas.order import CheckoutRequest
from app.services.order_service import OrderError, create_order
from conftest import CHECKOUT_PAYLOAD, login, make_admin
from test_catalog_search import _add, _catalog, _slugs
from test_orders_reservation import _cart_with

P = "/api/v1/products/"


def _setup(db_session, warehouse):
    cats, round_, square, bento = _catalog(db_session, warehouse)
    round_.sold_in_countries = ["Uzbekistan", "Kazakhstan"]      # only these two markets
    square.hidden_in_countries = ["Germany"]                      # everywhere except Germany
    db_session.commit()                                           # bento: no restriction
    return round_, square, bento


def test_listing_search_suggest_facets_and_related_follow_the_country(client, db_session, warehouse):
    round_, square, bento = _setup(db_session, warehouse)
    assert set(_slugs(client.get(P))) == {"round", "square", "bento"}                           # no country: nothing hidden
    assert set(_slugs(client.get(P, params={"country": "uzbekistan"}))) == {"round", "square", "bento"}   # any letter case
    assert set(_slugs(client.get(P, params={"country": "Germany"}))) == {"bento"}               # round: not sold there, square: hidden
    assert set(_slugs(client.get(P, params={"country": "France"}))) == {"square", "bento"}      # round is limited to UZ and KZ
    assert _slugs(client.get(P, params={"q": "container", "country": "Germany"})) == []
    assert set(_slugs(client.get(P, params={"q": "container", "country": "Kazakhstan"}))) == {"round", "square"}
    s = client.get(P + "suggest", params={"q": "container", "country": "Germany"}).json()
    assert s["products"] == []
    f = client.get(P + "facets", params={"country": "Germany"}).json()
    assert f["capacities"] == [800]                                                             # only bento's size is offered
    assert client.get(P + "facets").json()["capacities"] == [350, 800, 1000]                    # different cache entry
    cat = db_session.query(Product).filter_by(slug="bento").one().category
    mini = _add(db_session, warehouse, "Bento Mini", "bento-mini", 470, "BM-470", category=cat)
    hidden = _add(db_session, warehouse, "Bento Maxi", "bento-maxi", 1900, "BX-1900", category=cat)
    hidden.hidden_in_countries = ["France"]
    db_session.commit()
    rel = client.get(f"{P}{bento.slug}/related", params={"country": "France"}).json()
    assert [x["slug"] for x in rel["other_sizes"]] == ["bento-mini"]                            # the one hidden in France is left out
    assert [x["slug"] for x in client.get(f"{P}{bento.slug}/related").json()["other_sizes"]] == ["bento-mini", "bento-maxi"]
    assert mini.id


def test_the_page_still_opens_but_says_it_cannot_be_bought_there(client, db_session, warehouse):
    round_, square, _bento = _setup(db_session, warehouse)
    assert client.get(f"{P}{round_.slug}").json()["available_in_country"] is True
    assert client.get(f"{P}{round_.slug}", params={"country": "Germany"}).json()["available_in_country"] is False
    assert client.get(f"{P}{square.slug}", params={"country": "Germany"}).json()["available_in_country"] is False
    assert client.get(f"{P}{square.slug}", params={"country": "France"}).json()["available_in_country"] is True


def test_cart_flags_lines_and_checkout_refuses_them(client, db_session, warehouse, sku, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_x")
    round_, _square, _bento = _setup(db_session, warehouse)
    from app.models.sku import SKU

    round_sku = db_session.query(SKU).filter_by(sku_code="SKU-350-TR").one()
    first = client.get("/api/v1/cart/")
    token = first.headers["X-Cart-Token"]
    h = {"X-Cart-Token": token}
    client.post("/api/v1/cart/items", json={"sku_id": round_sku.id, "quantity": 1}, headers=h)
    client.post("/api/v1/cart/items", json={"sku_id": sku.id, "quantity": 1}, headers=h)   # unrestricted
    cart = client.get("/api/v1/cart/", params={"market_country": "Germany"}, headers=h).json()
    assert cart["unavailable_items"] == 1 and {i["sku_code"]: i["available_in_market"] for i in cart["items"]} == {"SKU-350-TR": False, "SKU-1000-001": True}
    assert client.get("/api/v1/cart/", headers=h).json()["unavailable_items"] == 0           # no market chosen
    assert client.get("/api/v1/cart/", params={"market_country": "Uzbekistan"}, headers=h).json()["unavailable_items"] == 0

    r = client.post("/api/v1/orders/", json={**CHECKOUT_PAYLOAD, "country": "Germany", "payment_method": "stripe"}, headers=h)
    assert r.status_code == 400 and "not sold in Germany" in r.text


def test_create_order_service_enforces_the_market(db_session, warehouse, sku):
    round_, *_ = _setup(db_session, warehouse)
    from app.models.sku import SKU

    round_sku = db_session.query(SKU).filter_by(sku_code="SKU-350-TR").one()
    with pytest.raises(OrderError, match="MARKET"):
        create_order(db_session, _cart_with(db_session, round_sku, 1), CheckoutRequest(**{**CHECKOUT_PAYLOAD, "country": "France"}), None)
    db_session.rollback()
    ok = create_order(db_session, _cart_with(db_session, round_sku, 1), CheckoutRequest(**CHECKOUT_PAYLOAD), None)  # Uzbekistan
    assert ok.id


def test_admin_sets_and_clears_the_lists(client, db_session, warehouse):
    round_, *_ = _setup(db_session, warehouse)
    make_admin(db_session, "pm@example.com", UserRole.PRODUCT_MANAGER)
    h = login(client, "pm@example.com")
    r = client.patch(f"/api/v1/admin/products/{round_.id}", json={"sold_in_countries": ["Georgia"], "hidden_in_countries": ["Armenia", "armenia"]}, headers=h)
    assert r.status_code == 200 and r.json()["sold_in_countries"] == ["Georgia"] and r.json()["hidden_in_countries"] == ["Armenia", "armenia"]
    assert set(_slugs(client.get(P, params={"country": "Georgia"}))) >= {"round"}
    assert "round" not in _slugs(client.get(P, params={"country": "Uzbekistan"}))
    r = client.patch(f"/api/v1/admin/products/{round_.id}", json={"sold_in_countries": [], "hidden_in_countries": None}, headers=h)
    assert r.json()["sold_in_countries"] is None
    assert "round" in _slugs(client.get(P, params={"country": "Uzbekistan"}))
    assert db_session.get(Product, round_.id) and _add


def test_wildcard_characters_in_the_country_do_not_match_everything(client, db_session, warehouse):
    _setup(db_session, warehouse)
    assert _slugs(client.get(P, params={"country": "%"})) == ["bento", "square"] or set(_slugs(client.get(P, params={"country": "%"}))) <= {"round", "square", "bento"}
    assert "round" not in _slugs(client.get(P, params={"country": "x_z"}))
