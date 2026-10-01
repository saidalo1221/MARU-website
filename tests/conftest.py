"""Shared fixtures for the whole suite.

Runs against SQLite, not MariaDB (this dev environment can't reach the real
UzCloud MariaDB — see TODO.md), with a compiler patch for the one behavior
difference that matters here: SQLite only treats a bare `INTEGER PRIMARY
KEY` as an autoincrement rowid alias, so every model's `BigInteger` PK needs
mapping to plain `INTEGER` to insert without an explicit id. MariaDB has no
such quirk, so this patch only takes effect under the `sqlite` dialect.

Env vars below must be set before the first `import app...` anywhere, since
`app.config.settings` is a module-level singleton built once at import time.
Actual process environment variables take priority over `.env` file values
(pydantic-settings' default), so this reliably overrides whatever the real
`.env` has, including a real MariaDB DATABASE_URL.
"""

import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["PAYME_MERCHANT_ID"] = "test-merchant"
os.environ["PAYME_KEY"] = "test-payme-key"
os.environ["CLICK_SERVICE_ID"] = "test-service"
os.environ["CLICK_MERCHANT_ID"] = "test-click-merchant"
os.environ["CLICK_SECRET_KEY"] = "test-click-secret"
os.environ["BITRIX24_WEBHOOK_URL"] = ""
os.environ["REDIS_URL"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@compiles(BigInteger, "sqlite")
def _bigint_as_integer(type_, compiler, **kw):
    return "INTEGER"


import app.models  # noqa: E402,F401 - registers every model on Base.metadata
from app.database import Base, get_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.inventory import Inventory  # noqa: E402
from app.models.product import Product  # noqa: E402
from app.models.product_variant import ProductVariant  # noqa: E402
from app.models.shipping_rate import ShippingRate  # noqa: E402
from app.models.sku import SKU  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.warehouse import Warehouse  # noqa: E402


@pytest.fixture()
def engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture()
def db_session(engine):
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_local()
    yield session
    session.close()


@pytest.fixture()
def client(engine):
    """A TestClient plus a matching DB session, both bound to the same
    per-test in-memory SQLite database (StaticPool keeps one connection for
    the whole engine, so writes through `client`'s override are visible to
    a `db_session` fixture used in the same test, and vice versa)."""
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = session_local()
        try:
            yield db
        finally:
            db.close()

    import app.main as main

    main.app.dependency_overrides[get_db] = override_get_db
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _reset_module_level_state():
    """Several modules keep process-global state that would otherwise leak
    between tests (each test here gets a fresh DB, but not a fresh process):
    the in-process rate limiter's hit-counters and cached Redis client."""
    import app.core.rate_limit as rate_limit_module

    rate_limit_module._hits.clear()
    rate_limit_module._redis_client = None
    rate_limit_module._redis_warned = False
    yield
    rate_limit_module._hits.clear()
    rate_limit_module._redis_client = None
    rate_limit_module._redis_warned = False


@pytest.fixture(autouse=True)
def _no_real_email(monkeypatch):
    """The developer's .env may hold real SMTP credentials; without this every
    registration in a test would try to send actual mail."""
    from app.config import settings

    monkeypatch.setattr(settings, "SMTP_HOST", None)


@pytest.fixture()
def warehouse(db_session):
    wh = Warehouse(name="Main", country="Uzbekistan", priority=1)
    db_session.add(wh)
    db_session.commit()
    return wh


@pytest.fixture()
def sku(db_session, warehouse):
    """One active SKU with 10 units of stock at `warehouse`, plus a
    wildcard shipping rate so checkout doesn't need one configured per test."""
    category = Category(name="Containers", slug="containers")
    db_session.add(category)
    db_session.flush()
    product = Product(category_id=category.id, name="Food Container", slug="food-container", volume_ml=1000)
    db_session.add(product)
    db_session.flush()
    variant = ProductVariant(product_id=product.id, name="1000ml", color="clear")
    db_session.add(variant)
    db_session.flush()
    sku_row = SKU(variant_id=variant.id, sku_code="SKU-1000-001", retail_price=10, currency="USD")
    db_session.add(sku_row)
    db_session.flush()
    db_session.add(Inventory(sku_id=sku_row.id, warehouse_id=warehouse.id, stock=10, reserved=0))
    db_session.add(ShippingRate(country="*", delivery_method="*", base_fee=0, per_kg_fee=0))
    db_session.commit()
    return sku_row


CHECKOUT_PAYLOAD = {
    "order_type": "individual",
    "first_name": "Alice",
    "last_name": "Doe",
    "phone": "+998900000000",
    "email": "alice@example.com",
    "country": "Uzbekistan",
    "city": "Tashkent",
    "address_line": "Main St 1",
    "postal_code": "100000",
    "delivery_method": "*",
    "payment_method": "payme",
    "source": "website",
}


def register(client: TestClient, email: str, role: UserRole = UserRole.CUSTOMER, password: str = "Password123!") -> dict:
    """Registers a customer account through the real HTTP endpoint, then
    (if role != CUSTOMER) promotes it directly in the DB — there's no signup
    flow for admin accounts, matching how they're actually provisioned."""
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    if role != UserRole.CUSTOMER:
        _promote(client, email, role)
    return {"Authorization": f"Bearer {token}"}


def _promote(client: TestClient, email: str, role: UserRole) -> None:
    import app.main as main

    db_dependency = main.app.dependency_overrides[get_db]
    db = next(db_dependency())
    try:
        user = db.query(User).filter_by(email=email).one()
        user.role = role
        db.commit()
    finally:
        db.close()


def login(client: TestClient, email: str, password: str = "Password123!") -> dict:
    """Signs in through the real endpoints, completing the emailed-code step
    each account type requires: admin roles go through /auth/admin/login +
    /auth/admin/verify, customers through the new-device challenge
    (/auth/login + /auth/login/verify-device). The code is captured by
    swapping the notifier's send method, since only its hash is stored."""
    import app.routers.auth as auth_router

    notifier = auth_router.email_notifier
    captured: dict = {}
    originals = {}
    for name in ("admin_login_code", "device_login_code"):
        originals[name] = getattr(notifier, name)
        setattr(notifier, name, lambda to_email, code, db=None, _n=name: captured.update({_n: code}))
    try:
        r = client.post("/api/v1/auth/admin/login", json={"email": email, "password": password})
        if r.status_code == 200:
            r = client.post("/api/v1/auth/admin/verify", json={"email": email, "code": captured["admin_login_code"]})
        else:
            device_id = "test-device"
            r = client.post("/api/v1/auth/login", json={"email": email, "password": password, "device_id": device_id})
            assert r.status_code == 200, r.text
            if not r.json().get("access_token"):
                r = client.post(
                    "/api/v1/auth/login/verify-device",
                    json={"email": email, "code": captured["device_login_code"], "device_id": device_id},
                )
    finally:
        for name, fn in originals.items():
            setattr(notifier, name, fn)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def make_admin(db_session, email: str, role: UserRole, password: str = "Password123!") -> User:
    user = User(email=email, password_hash=hash_password(password), role=role, is_active=True)
    db_session.add(user)
    db_session.commit()
    return user
