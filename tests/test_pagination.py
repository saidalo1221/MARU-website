"""List endpoints page their results with a hard maximum size (PRD ТЗ№3 §51)."""

from app.models.enums import OrderStatus, UserRole
from app.models.review import Review
from app.models.user import User
from app.schemas.order import CheckoutRequest
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.services.order_service import create_order
from conftest import CHECKOUT_PAYLOAD, login, make_admin, register


def _orders(db_session, sku, n):
    for i in range(n):
        cart = Cart(token=f"page-{i}")
        db_session.add(cart)
        db_session.flush()
        db_session.add(CartItem(cart_id=cart.id, sku_id=sku.id, quantity=1))
        db_session.commit()
        db_session.refresh(cart)
        create_order(db_session, cart, CheckoutRequest(**CHECKOUT_PAYLOAD), None)
        db_session.commit()


def test_admin_orders_are_paged_with_a_total(client, db_session, sku):
    _orders(db_session, sku, 5)
    make_admin(db_session, "sales@example.com", UserRole.SALES_MANAGER)
    h = login(client, "sales@example.com")
    first = client.get("/api/v1/admin/orders/", params={"limit": 2}, headers=h)
    assert first.status_code == 200
    assert len(first.json()) == 2 and first.headers["X-Total-Count"] == "5"
    last = client.get("/api/v1/admin/orders/", params={"limit": 2, "page": 3}, headers=h)
    assert len(last.json()) == 1
    ids = [o["id"] for o in first.json()] + [o["id"] for o in client.get("/api/v1/admin/orders/", params={"limit": 2, "page": 2}, headers=h).json()] + [o["id"] for o in last.json()]
    assert len(set(ids)) == 5  # no overlap between pages
    assert client.get("/api/v1/admin/orders/", params={"status_filter": "new"}, headers=h).headers["X-Total-Count"] == "5"
    assert client.get("/api/v1/admin/orders/", params={"status_filter": "paid"}, headers=h).headers["X-Total-Count"] == "0"


def test_page_size_has_a_hard_maximum(client, db_session):
    make_admin(db_session, "sales2@example.com", UserRole.SALES_MANAGER)
    h = login(client, "sales2@example.com")
    for path in ("/api/v1/admin/orders/", "/api/v1/admin/quotes/", "/api/v1/admin/reviews/", "/api/v1/admin/blog/posts"):
        assert client.get(path, params={"limit": 101}, headers=h).status_code in (403, 422), path
    # The roles above may not reach every route; the SALES_MANAGER ones must reject limit=101.
    assert client.get("/api/v1/admin/orders/", params={"limit": 101}, headers=h).status_code == 422
    assert client.get("/api/v1/admin/quotes/", params={"limit": 0}, headers=h).status_code == 422
    assert client.get("/api/v1/admin/quotes/", params={"page": 0}, headers=h).status_code == 422


def test_my_orders_are_paged(client, db_session, sku):
    headers = register(client, "frequent@example.com")
    uid = db_session.query(User).filter_by(email="frequent@example.com").one().id
    _orders(db_session, sku, 3)
    from app.models.order import Order

    for order in db_session.query(Order).all():
        order.user_id = uid
    db_session.commit()
    r = client.get("/api/v1/orders/me", params={"limit": 2}, headers=headers)
    assert len(r.json()) == 2 and r.headers["X-Total-Count"] == "3"
    assert client.get("/api/v1/orders/me", params={"limit": 500}, headers=headers).status_code == 422
