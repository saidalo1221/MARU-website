"""Registration, login, email verification, password reset, and admin MFA
(PRD ТЗ№3 §55-58)."""

import pyotp

from conftest import register


def test_register_and_login(client):
    headers = register(client, "person@example.com")
    r = client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "person@example.com"
    assert r.json()["email_verified"] is False


def test_duplicate_registration_rejected(client):
    register(client, "dupe@example.com")
    r = client.post("/api/v1/auth/register", json={"email": "dupe@example.com", "password": "Password123!"})
    assert r.status_code == 400


def test_login_wrong_password_rejected(client):
    register(client, "person2@example.com")
    r = client.post("/api/v1/auth/login", json={"email": "person2@example.com", "password": "WrongPassword"})
    assert r.status_code == 401


def test_email_verification_flow(client, monkeypatch):
    captured = {}

    def fake_email_verification(self, to_email, token, db=None):
        captured["token"] = token

    import app.services.notifications.email as email_module

    monkeypatch.setattr(email_module.EmailNotifier, "email_verification", fake_email_verification)

    headers = register(client, "verify@example.com")
    assert "token" in captured

    r = client.post("/api/v1/auth/verify-email", json={"token": "wrong-token"})
    assert r.status_code == 400

    r = client.post("/api/v1/auth/verify-email", json={"token": captured["token"]})
    assert r.status_code == 200

    r = client.get("/api/v1/auth/me", headers=headers)
    assert r.json()["email_verified"] is True

    # Token can't be reused.
    r = client.post("/api/v1/auth/verify-email", json={"token": captured["token"]})
    assert r.status_code == 400


def test_password_reset_flow(client, monkeypatch):
    captured = {}

    def fake_password_reset(self, to_email, token, db=None):
        captured["token"] = token

    import app.services.notifications.email as email_module

    monkeypatch.setattr(email_module.EmailNotifier, "password_reset", fake_password_reset)

    register(client, "forgetful@example.com")
    r = client.post("/api/v1/auth/forgot-password", json={"email": "forgetful@example.com"})
    assert r.status_code == 200
    assert "token" in captured

    r = client.post(
        "/api/v1/auth/reset-password", json={"token": captured["token"], "new_password": "NewPassword123!"}
    )
    assert r.status_code == 200

    r = client.post("/api/v1/auth/login", json={"email": "forgetful@example.com", "password": "NewPassword123!"})
    assert r.status_code == 200


def test_forgot_password_does_not_reveal_whether_email_exists(client):
    r1 = client.post("/api/v1/auth/forgot-password", json={"email": "exists@example.com"})
    r2 = client.post("/api/v1/auth/forgot-password", json={"email": "doesnotexist@example.com"})
    assert r1.status_code == r2.status_code == 200
    assert r1.json() == r2.json()


def test_mfa_setup_enable_enforce_disable(client):
    headers = register(client, "mfauser@example.com")

    r = client.post("/api/v1/auth/mfa/setup", headers=headers)
    assert r.status_code == 200, r.text
    secret = r.json()["secret"]

    r = client.post("/api/v1/auth/mfa/enable", headers=headers, json={"code": "000000"})
    assert r.status_code == 400

    code = pyotp.TOTP(secret).now()
    r = client.post("/api/v1/auth/mfa/enable", headers=headers, json={"code": code})
    assert r.status_code == 200

    # Login now requires the code.
    r = client.post("/api/v1/auth/login", json={"email": "mfauser@example.com", "password": "Password123!"})
    assert r.status_code == 401

    code = pyotp.TOTP(secret).now()
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "mfauser@example.com", "password": "Password123!", "mfa_code": code},
    )
    assert r.status_code == 200

    code = pyotp.TOTP(secret).now()
    r = client.post("/api/v1/auth/mfa/disable", headers=headers, json={"code": code})
    assert r.status_code == 200

    r = client.post("/api/v1/auth/login", json={"email": "mfauser@example.com", "password": "Password123!"})
    assert r.status_code == 200
