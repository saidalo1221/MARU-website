"""Uniform error body (PRD ТЗ№3 §50): a stable `error` object next to the legacy `detail`."""

from fastapi.testclient import TestClient

from app.core.errors import error_code_for


def test_codes_are_derived_from_status_and_coded_details():
    assert error_code_for(404, "Order not found") == ("NOT_FOUND", "Order not found")
    assert error_code_for(409, "INSUFFICIENT_STOCK: not enough stock for SKU X") == ("INSUFFICIENT_STOCK", "not enough stock for SKU X")
    assert error_code_for(429, "Too many requests")[0] == "RATE_LIMITED"
    assert error_code_for(422, [{"msg": "field required"}, {"msg": "too short"}]) == ("VALIDATION_ERROR", "field required; too short")
    assert error_code_for(503, "x")[0] == "SERVICE_UNAVAILABLE"


def test_http_errors_carry_code_message_and_request_id(client):
    r = client.get("/api/v1/products/does-not-exist", headers={"X-Request-ID": "req-abc-12345"})
    assert r.status_code == 404
    body = r.json()
    assert body["detail"] == "Product not found"  # legacy shape kept
    assert body["error"] == {"code": "NOT_FOUND", "message": "Product not found", "request_id": "req-abc-12345"}
    assert r.headers["X-Request-ID"] == "req-abc-12345"


def test_validation_errors_use_the_same_shape(client):
    r = client.post("/api/v1/auth/register", json={"email": "not-an-email", "password": "x"})
    assert r.status_code == 422
    body = r.json()
    assert isinstance(body["detail"], list)
    assert body["error"]["code"] == "VALIDATION_ERROR" and body["error"]["request_id"]


def test_business_error_codes_reach_the_client(client, sku):
    client.post("/api/v1/cart/items", json={"sku_id": sku.id, "quantity": 1})
    too_many = client.post("/api/v1/cart/items", json={"sku_id": sku.id, "quantity": 999})
    assert too_many.status_code == 400
    assert too_many.json()["error"]["code"] == "INSUFFICIENT_STOCK"


def test_unhandled_exceptions_return_a_generic_500_without_a_stack_trace(client):
    app = client.app

    @app.get("/__boom")
    def boom():
        raise RuntimeError("secret internal detail /srv/app/db.py line 42")

    quiet = TestClient(app, raise_server_exceptions=False)
    r = quiet.get("/__boom")
    assert r.status_code == 500
    assert "secret" not in r.text and "Traceback" not in r.text
    body = r.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["request_id"] and body["error"]["request_id"] != "-"
    assert r.headers["X-Request-ID"] == body["error"]["request_id"]
