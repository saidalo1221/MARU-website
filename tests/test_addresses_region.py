"""Saved addresses carry an optional region (selects region tax rules)."""

from conftest import register

ADDRESS = {
    "first_name": "Ali", "last_name": "Valiyev", "phone": "+998901234567", "country": "Uzbekistan",
    "city": "Tashkent", "address_line": "Chilonzor 12", "postal_code": "100000",
}


def test_region_is_saved_trimmed_and_returned(client):
    h = register(client, "addr@example.com")
    r = client.post("/api/v1/addresses/", json={**ADDRESS, "region": "  Tashkent region "}, headers=h)
    assert r.status_code == 201, r.text
    assert r.json()["region"] == "Tashkent region"
    assert client.get("/api/v1/addresses/", headers=h).json()[0]["region"] == "Tashkent region"


def test_region_is_optional_and_blank_becomes_null(client):
    h = register(client, "addr2@example.com")
    assert client.post("/api/v1/addresses/", json=ADDRESS, headers=h).json()["region"] is None
    assert client.post("/api/v1/addresses/", json={**ADDRESS, "region": "   "}, headers=h).json()["region"] is None


def test_region_can_be_changed_and_cleared(client):
    h = register(client, "addr3@example.com")
    aid = client.post("/api/v1/addresses/", json={**ADDRESS, "region": "Samarkand"}, headers=h).json()["id"]
    r = client.put(f"/api/v1/addresses/{aid}", json={**ADDRESS, "region": "Bukhara"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["region"] == "Bukhara"
    assert client.put(f"/api/v1/addresses/{aid}", json=ADDRESS, headers=h).json()["region"] is None
