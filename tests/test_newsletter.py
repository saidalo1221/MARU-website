"""Double opt-in newsletter signup (PRD ТЗ№2 §43)."""

import pytest

from app.models.enums import UserRole
from app.models.newsletter_subscriber import NewsletterStatus, NewsletterSubscriber
from conftest import login, make_admin, register


@pytest.fixture()
def sent(monkeypatch):
    import app.routers.newsletter as newsletter

    emails = []
    monkeypatch.setattr(newsletter.notifier, "newsletter_confirmation", lambda to, token, db=None: emails.append((to, token)))
    return emails


def _subscribe(client, email="Reader@Example.com", **extra):
    return client.post("/api/v1/newsletter/subscribe", json={"email": email, **extra})


def test_subscribe_creates_pending_row_and_sends_confirmation(client, db_session, sent):
    r = _subscribe(client, locale="ru")
    assert r.status_code == 202
    row = db_session.query(NewsletterSubscriber).one()
    assert (row.email, row.status, row.locale) == ("reader@example.com", NewsletterStatus.PENDING, "ru")
    assert sent == [("reader@example.com", row.token)]


def test_confirm_then_unsubscribe_with_token(client, db_session, sent):
    _subscribe(client)
    token = sent[0][1]
    assert client.post("/api/v1/newsletter/confirm", json={"token": token}).status_code == 200
    db_session.expire_all()
    row = db_session.query(NewsletterSubscriber).one()
    assert row.status == NewsletterStatus.CONFIRMED and row.confirmed_at is not None

    assert client.post("/api/v1/newsletter/unsubscribe", json={"token": token}).status_code == 200
    db_session.expire_all()
    assert db_session.query(NewsletterSubscriber).one().status == NewsletterStatus.UNSUBSCRIBED


def test_unconfirmed_signup_stays_pending_and_bad_token_is_404(client, db_session, sent):
    _subscribe(client)
    assert db_session.query(NewsletterSubscriber).one().status == NewsletterStatus.PENDING
    assert client.post("/api/v1/newsletter/confirm", json={"token": "x" * 40}).status_code == 404
    assert client.post("/api/v1/newsletter/unsubscribe", json={"token": "x" * 40}).status_code == 404


def test_already_confirmed_address_gets_same_answer_and_no_email(client, db_session, sent):
    _subscribe(client)
    client.post("/api/v1/newsletter/confirm", json={"token": sent[0][1]})
    sent.clear()
    r = _subscribe(client)
    assert r.status_code == 202 and r.json() == {"status": "ok"}
    assert sent == []  # nothing revealed, nothing sent


def test_resubscribing_after_unsubscribe_requires_reconfirmation(client, db_session, sent):
    _subscribe(client)
    token = sent[0][1]
    client.post("/api/v1/newsletter/confirm", json={"token": token})
    client.post("/api/v1/newsletter/unsubscribe", json={"token": token})
    _subscribe(client)
    db_session.expire_all()
    assert db_session.query(NewsletterSubscriber).one().status == NewsletterStatus.PENDING
    assert len(sent) == 2


def test_subscribe_validates_email_and_is_rate_limited(client, sent):
    assert _subscribe(client, email="not-an-email").status_code == 422
    for i in range(5):
        _subscribe(client, email=f"user{i}@example.com")
    assert _subscribe(client, email="user9@example.com").status_code == 429


def test_unknown_locale_falls_back_to_english(client, db_session, sent):
    _subscribe(client, locale="xx")
    assert db_session.query(NewsletterSubscriber).one().locale == "en"


def test_admin_list_requires_marketing_role_and_reports_counts(client, db_session, sent):
    _subscribe(client)
    _subscribe(client, email="second@example.com")
    client.post("/api/v1/newsletter/confirm", json={"token": sent[0][1]})

    assert client.get("/api/v1/admin/newsletter/").status_code in (401, 403)
    assert client.get("/api/v1/admin/newsletter/", headers=register(client, "cust@example.com")).status_code == 403

    make_admin(db_session, "mkt@example.com", UserRole.MARKETING_MANAGER)
    headers = login(client, "mkt@example.com")
    body = client.get("/api/v1/admin/newsletter/", headers=headers).json()
    assert body["counts"] == {"confirmed": 1, "pending": 1}
    assert len(body["subscribers"]) == 2
    only = client.get("/api/v1/admin/newsletter/?status_filter=confirmed", headers=headers).json()
    assert [s["email"] for s in only["subscribers"]] == ["reader@example.com"]
    assert "token" not in only["subscribers"][0]
