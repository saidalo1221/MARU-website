"""Notification templates override the hardcoded fallback (PRD ТЗ№4 §42)."""

from app.models.enums import UserRole
from app.models.notification_template import NotificationTemplate
from app.services.notifications.email import EmailNotifier
from app.services.notifications.templates import render_template
from conftest import login, make_admin


class _FakeOrder:
    order_number = "MARU-1"
    first_name = "Alice"
    total_amount = "10.00"
    currency = "USD"
    email = "a@example.com"


def test_falls_back_to_hardcoded_copy_with_no_rows(db_session):
    captured = {}
    notifier = EmailNotifier()
    notifier._send = lambda to, subject, body: captured.update(to=to, subject=subject, body=body)

    notifier.order_created(_FakeOrder(), db=db_session)
    assert "MARU-1" in captured["subject"]


def test_db_template_overrides_hardcoded_copy(db_session):
    db_session.add(
        NotificationTemplate(
            event="order_created", locale="en", channel="email",
            subject="[MARU] Order {order_number} received!",
            body="Thanks {first_name}, your order {order_number} for {total_amount} {currency} is in.",
        )
    )
    db_session.commit()

    captured = {}
    notifier = EmailNotifier()
    notifier._send = lambda to, subject, body: captured.update(to=to, subject=subject, body=body)
    notifier.order_created(_FakeOrder(), db=db_session)

    assert captured["subject"] == "[MARU] Order MARU-1 received!"
    assert "Thanks Alice" in captured["body"]


def test_locale_falls_back_to_english_row(db_session):
    db_session.add(
        NotificationTemplate(event="order_created", locale="en", channel="email", body="EN: {order_number}")
    )
    db_session.commit()

    result = render_template(db_session, "order_created", {"order_number": "X"}, locale="ru")
    assert result == ("", "EN: X")


def test_malformed_template_falls_back_safely(db_session):
    db_session.add(NotificationTemplate(event="order_created", locale="en", channel="email", body="{missing_field}"))
    db_session.commit()

    assert render_template(db_session, "order_created", {"order_number": "X"}, locale="en") is None


def test_inactive_template_is_ignored(db_session):
    db_session.add(
        NotificationTemplate(event="order_created", locale="en", channel="email", body="x", is_active=False)
    )
    db_session.commit()
    assert render_template(db_session, "order_created", {}, locale="en") is None


def test_admin_notification_template_crud(client, db_session):
    make_admin(db_session, "marketing@example.com", UserRole.MARKETING_MANAGER)
    headers = login(client, "marketing@example.com")

    r = client.post(
        "/api/v1/admin/notification-templates/", headers=headers,
        json={"event": "order_created", "locale": "en", "body": "Hi {first_name}!"},
    )
    assert r.status_code == 201, r.text
    template_id = r.json()["id"]

    r = client.post(
        "/api/v1/admin/notification-templates/", headers=headers,
        json={"event": "order_created", "locale": "en", "body": "dup"},
    )
    assert r.status_code == 409

    r = client.patch(
        f"/api/v1/admin/notification-templates/{template_id}", headers=headers, json={"body": "Updated"}
    )
    assert r.status_code == 200 and r.json()["body"] == "Updated"
