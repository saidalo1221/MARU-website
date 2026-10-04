"""PRD ТЗ№1 §33: admins manage customers (retail / B2B / distributors)."""

from app.models.enums import CustomerType, OrderStatus, UserRole
from app.models.user import User
from app.schemas.order import CheckoutRequest
from app.services.order_service import create_order
from conftest import CHECKOUT_PAYLOAD, login, make_admin, register
from test_orders_reservation import _cart_with

API = "/api/v1/admin/customers"


def test_list_search_filter_and_order_counts(client, db_session, sku):
    register(client, "alice@example.com")
    register(client, "bob@example.com")
    alice = db_session.query(User).filter_by(email="alice@example.com").one()
    create_order(db_session, _cart_with(db_session, sku, 1), CheckoutRequest(**CHECKOUT_PAYLOAD), alice)
    db_session.commit()
    make_admin(db_session, "sales@example.com", UserRole.SALES_MANAGER)
    h = login(client, "sales@example.com")

    rows = client.get(API + "/", headers=h).json()
    assert {r["email"] for r in rows} == {"alice@example.com", "bob@example.com"}  # staff are not listed
    assert {r["email"]: r["order_count"] for r in rows} == {"alice@example.com": 1, "bob@example.com": 0}
    assert [r["email"] for r in client.get(API + "/?q=ALI", headers=h).json()] == ["alice@example.com"]
    assert client.get(API + "/?customer_type=wholesale", headers=h).json() == []


def test_change_type_and_deactivate_are_audited_and_staff_are_off_limits(client, db_session):
    register(client, "alice@example.com")
    alice = db_session.query(User).filter_by(email="alice@example.com").one()
    make_admin(db_session, "sales@example.com", UserRole.SALES_MANAGER)
    staff = db_session.query(User).filter_by(email="sales@example.com").one()
    h = login(client, "sales@example.com")

    r = client.patch(f"{API}/{alice.id}", json={"customer_type": "wholesale"}, headers=h)
    assert r.status_code == 200 and r.json()["customer_type"] == "wholesale"
    assert client.patch(f"{API}/{alice.id}", json={"is_active": False}, headers=h).json()["is_active"] is False
    assert client.patch(f"{API}/{staff.id}", json={"customer_type": "export"}, headers=h).status_code == 404
    assert client.patch(f"{API}/{alice.id}", json={"customer_type": "bogus"}, headers=h).status_code == 422

    from app.models.audit_log import AuditLog
    db_session.expire_all()
    assert db_session.query(AuditLog).filter_by(action="customer_update").count() == 2
    assert db_session.get(User, alice.id).customer_type == CustomerType.WHOLESALE


def test_customers_and_unprivileged_roles_cannot_use_it(client, db_session):
    register(client, "alice@example.com")
    assert client.get(API + "/").status_code == 401
    assert client.get(API + "/", headers=login(client, "alice@example.com")).status_code == 403
    make_admin(db_session, "w@example.com", UserRole.WAREHOUSE_MANAGER)
    assert client.get(API + "/", headers=login(client, "w@example.com")).status_code == 403
    assert OrderStatus.NEW
