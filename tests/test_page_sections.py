

def test_faq_sections_can_be_grouped_by_topic(client, db_session):
    from app.models.enums import UserRole
    from conftest import login, make_admin

    make_admin(db_session, "mkt@example.com", UserRole.MARKETING_MANAGER)
    h = login(client, "mkt@example.com")
    base = "/api/v1/admin/page-sections"

    a = client.post(base, json={"page": "faq", "title": "Do you deliver abroad?", "body": "Yes.", "category": "international"}, headers=h)
    assert a.status_code == 201, a.text
    assert a.json()["category"] == "international"
    client.post(base, json={"page": "faq", "title": "Who are you?", "body": "MARU."}, headers=h)

    public = {s["title"]: s["category"] for s in client.get("/api/v1/page-sections", params={"page": "faq"}).json()}
    assert public == {"Do you deliver abroad?": "international", "Who are you?": None}

    # Changing and clearing the topic.
    sid = a.json()["id"]
    assert client.patch(f"{base}/{sid}", json={"category": "payment"}, headers=h).json()["category"] == "payment"
    assert client.patch(f"{base}/{sid}", json={"category": None}, headers=h).json()["category"] is None

    # Only FAQ sections have a topic, and only known topics are accepted.
    assert client.post(base, json={"page": "delivery", "title": "x", "body": "y", "category": "orders"}, headers=h).status_code == 400
    assert client.post(base, json={"page": "faq", "title": "x", "body": "y", "category": "weather"}, headers=h).status_code == 422
