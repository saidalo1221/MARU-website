"""Baseline security headers and the /docs exposure switch."""


def test_api_responses_carry_security_headers(client):
    r = client.get("/api/v1/exchange-rates/")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "max-age" in r.headers["Strict-Transport-Security"]
    assert "frame-ancestors 'none'" in r.headers["Content-Security-Policy"]


def test_error_responses_also_carry_headers(client):
    r = client.get("/api/v1/does-not-exist")
    assert r.status_code == 404
    assert r.headers["X-Content-Type-Options"] == "nosniff"


def test_swagger_and_openapi_are_off_by_default(client):
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404, path


def test_every_response_has_a_request_id_and_valid_incoming_ids_are_kept(client):
    generated = client.get("/api/v1/exchange-rates/").headers["X-Request-ID"]
    assert len(generated) == 32

    kept = client.get("/api/v1/exchange-rates/", headers={"X-Request-ID": "trace-abc-12345"})
    assert kept.headers["X-Request-ID"] == "trace-abc-12345"

    replaced = client.get("/api/v1/exchange-rates/", headers={"X-Request-ID": "bad id\twith junk"})
    assert replaced.headers["X-Request-ID"] != "bad id\twith junk"
    assert client.get("/api/v1/does-not-exist").headers["X-Request-ID"]


def test_log_records_carry_the_request_id(client, caplog):
    import logging

    from app.core.request_id import request_id_var

    token = request_id_var.set("req-under-test")
    try:
        logging.getLogger("maru.test").warning("hello")
    finally:
        request_id_var.reset(token)
    assert caplog.records[-1].request_id == "req-under-test"
