"""PRD ТЗ№3 §87: public reads are cached and a committed change drops the cache."""

from app.core import cache
from app.models.category import Category
from app.models.exchange_rate import ExchangeRate
from app.models.enums import UserRole
from conftest import login, make_admin


def test_ttl_and_manual_invalidation():
    calls = []
    assert cache.get_or_set("x", "k", 60, lambda: calls.append(1) or {"v": len(calls)}) == {"v": 1}
    assert cache.get_or_set("x", "k", 60, lambda: calls.append(1) or {"v": len(calls)}) == {"v": 1}
    cache.invalidate("x")
    assert cache.get_or_set("x", "k", 60, lambda: calls.append(1) or {"v": len(calls)}) == {"v": 2}
    assert cache.get_or_set("x", "k", 0, lambda: {"v": "uncached"}) == {"v": "uncached"}


def test_categories_cached_then_invalidated_by_any_commit(client, db_session):
    db_session.add(Category(name="Bottles", slug="bottles"))
    db_session.commit()
    assert [c["name"] for c in client.get("/api/v1/categories/").json()] == ["Bottles"]

    # Insert behind the cache's back with a raw statement: still the cached answer.
    db_session.execute(Category.__table__.insert().values(name="Caps", slug="caps"))
    db_session.commit()  # raw SQL does not touch the ORM change tracking
    assert [c["name"] for c in client.get("/api/v1/categories/").json()] == ["Bottles"]

    db_session.add(Category(name="Jars", slug="jars"))
    db_session.commit()  # an ORM change clears the namespace
    assert sorted(c["name"] for c in client.get("/api/v1/categories/").json()) == ["Bottles", "Caps", "Jars"]


def test_exchange_rates_refresh_after_admin_update(client, db_session):
    make_admin(db_session, "root@example.com", UserRole.SUPER_ADMIN)
    h = login(client, "root@example.com")
    r = client.post("/api/v1/admin/exchange-rates/", json={"currency": "EUR", "units_per_usd": "0.9"}, headers=h)
    assert r.status_code == 201, r.text
    first = client.get("/api/v1/exchange-rates/", headers=h).json()
    assert [x["currency"] for x in first] == ["EUR"]
    client.patch(f"/api/v1/admin/exchange-rates/{r.json()['id']}", json={"units_per_usd": "0.95"}, headers=h)
    again = client.get("/api/v1/exchange-rates/", headers=h).json()
    assert float(again[0]["units_per_usd"]) == 0.95
