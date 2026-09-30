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
