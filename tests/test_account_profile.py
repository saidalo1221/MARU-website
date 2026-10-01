"""Password policy, self-service profile edit and password change (PRD ТЗ№2 §27, ТЗ№3 §56/§58)."""

import pytest

from app.core.password_policy import PasswordPolicyError, validate_password
from app.models.enums import UserRole
from app.models.user import User
from conftest import login, make_admin, register

ME = "/api/v1/auth/me"


@pytest.mark.parametrize(
    "password",
    ["short1", "onlyletters", "12345678", "Password123", "x" * 129],  # too short, no digit, all digits, common, too long
)
def test_weak_customer_passwords_are_rejected(password):
    with pytest.raises(PasswordPolicyError):
        validate_password(password)


def test_customer_and_admin_policies():
    validate_password("Maru2026box")  # letters + digits, 8+ is enough for a customer
    for weak in ("Maru2026box", "alllowercase1!x"):
        with pytest.raises(PasswordPolicyError):
            validate_password(weak, strong=True)
    validate_password("Str0ng&Long-Pass", strong=True)
    with pytest.raises(PasswordPolicyError):
        validate_password("person@example.com1", email="PERSON@example.com1")


def test_register_rejects_weak_passwords(client):
    r = client.post("/api/v1/auth/register", json={"email": "weak@example.com", "password": "abc"})
    assert r.status_code == 400
    assert "at least 8" in r.json()["detail"]
    assert client.post("/api/v1/auth/register", json={"email": "ok@example.com", "password": "GoodPass123"}).status_code == 201


def test_profile_update_and_phone_normalisation(client):
    h = register(client, "prof@example.com")
    r = client.patch(ME, json={"first_name": "  Ali ", "last_name": "Valiyev", "phone": "+998 (90) 123-45-67"}, headers=h)
    assert r.status_code == 200, r.text
    assert (r.json()["first_name"], r.json()["last_name"], r.json()["phone"]) == ("Ali", "Valiyev", "+998901234567")
    assert client.get(ME, headers=h).json()["phone"] == "+998901234567"

    assert client.patch(ME, json={"phone": "12ab"}, headers=h).status_code == 422
    cleared = client.patch(ME, json={"phone": "  ", "last_name": ""}, headers=h).json()
    assert cleared["phone"] is None and cleared["last_name"] is None and cleared["first_name"] == "Ali"
    # Email and role are not editable through the profile endpoint.
    client.patch(ME, json={"email": "evil@example.com", "role": "super_admin"}, headers=h)
    me = client.get(ME, headers=h).json()
    assert me["email"] == "prof@example.com" and me["role"] == "customer"
    assert client.patch(ME, json={"first_name": "x"}).status_code in (401, 403)


def test_change_password(client, db_session):
    h = register(client, "chg@example.com", password="OldPassw0rd")
    url = "/api/v1/auth/change-password"
    assert client.post(url, json={"current_password": "wrong", "new_password": "NewPassw0rd"}, headers=h).status_code == 400
    assert client.post(url, json={"current_password": "OldPassw0rd", "new_password": "OldPassw0rd"}, headers=h).status_code == 400
    assert client.post(url, json={"current_password": "OldPassw0rd", "new_password": "weak"}, headers=h).status_code == 400
    ok = client.post(url, json={"current_password": "OldPassw0rd", "new_password": "NewPassw0rd"}, headers=h)
    assert ok.status_code == 200, ok.text
    assert login(client, "chg@example.com", password="NewPassw0rd")  # new password works
    assert client.post("/api/v1/auth/login", json={"email": "chg@example.com", "password": "OldPassw0rd", "device_id": "d"}).status_code != 200


def test_admin_roles_need_the_strong_policy_to_change_password(client, db_session):
    make_admin(db_session, "boss@example.com", UserRole.SUPER_ADMIN)
    h = login(client, "boss@example.com")
    url = "/api/v1/auth/change-password"
    short = client.post(url, json={"current_password": "Password123!", "new_password": "Maru2026box"}, headers=h)
    assert short.status_code == 400 and "12 characters" in short.json()["detail"]
    no_symbol = client.post(url, json={"current_password": "Password123!", "new_password": "Maru2026boxLong"}, headers=h)
    assert no_symbol.status_code == 400 and "Admin" in no_symbol.json()["detail"]
    strong = client.post(url, json={"current_password": "Password123!", "new_password": "Str0ng&Long-Pass"}, headers=h)
    assert strong.status_code == 200, strong.text
    assert db_session.query(User).filter_by(email="boss@example.com").one().role == UserRole.SUPER_ADMIN


def _unpaid_order(db_session, sku, user_id=None, method="payme", reference="https://checkout.example/pay/abc", status=None):
    from app.models.cart import Cart
    from app.models.cart_item import CartItem
    from app.schemas.order import CheckoutRequest
    from app.services.order_service import create_order
    from conftest import CHECKOUT_PAYLOAD

    cart = Cart(token=f"retry-{method}-{id(object())}")
    db_session.add(cart)
    db_session.flush()
    db_session.add(CartItem(cart_id=cart.id, sku_id=sku.id, quantity=1))
    db_session.commit()
    db_session.refresh(cart)
    order = create_order(db_session, cart, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
    order.payment_method = method
    order.payment_reference = reference
    order.user_id = user_id
    if status is not None:
        order.status = status
    db_session.commit()
    return order


def test_retry_payment_returns_the_link_for_unpaid_and_failed_orders(client, db_session, sku):
    from app.models.enums import OrderStatus

    h = register(client, "payer@example.com")
    uid = db_session.query(User).filter_by(email="payer@example.com").one().id
    order = _unpaid_order(db_session, sku, user_id=uid, status=OrderStatus.PAYMENT_FAILED)

    r = client.post(f"/api/v1/orders/{order.id}/payment", headers=h)
    assert r.status_code == 200, r.text
    assert r.json() == {"method": "payme", "reference_kind": "redirect_url", "reference": "https://checkout.example/pay/abc"}


def test_retry_payment_refuses_paid_card_and_foreign_orders(client, db_session, sku):
    from app.models.enums import OrderStatus

    h = register(client, "payer2@example.com")
    uid = db_session.query(User).filter_by(email="payer2@example.com").one().id
    paid = _unpaid_order(db_session, sku, user_id=uid, status=OrderStatus.PAID)
    assert client.post(f"/api/v1/orders/{paid.id}/payment", headers=h).status_code == 409

    card = _unpaid_order(db_session, sku, user_id=uid, method="stripe", reference="pi_secret_x")
    assert client.post(f"/api/v1/orders/{card.id}/payment", headers=h).status_code == 409

    other = register(client, "stranger@example.com")
    mine = _unpaid_order(db_session, sku, user_id=uid)
    assert client.post(f"/api/v1/orders/{mine.id}/payment", headers=other).status_code == 404
    assert client.post(f"/api/v1/orders/{mine.id}/payment").status_code == 404  # anonymous without the guest token
