from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_is_public_and_database_independent() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_database_ready() -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_health_returns_generated_correlation_id() -> None:
    response = client.get("/health")

    correlation_id = response.headers.get("X-Correlation-ID")

    assert response.status_code == 200
    assert correlation_id
    assert len(correlation_id) >= 16


def test_health_preserves_supplied_correlation_id() -> None:
    correlation_id = "m24-api-review-correlation-id"

    response = client.get(
        "/health",
        headers={"X-Correlation-ID": correlation_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == correlation_id


def test_cors_allows_configured_frontend_origin() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:5173"
    )


def test_cors_rejects_unconfigured_origin() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers


def test_openapi_exposes_health_and_readiness() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/health" in paths
    assert "/ready" in paths


def test_openapi_exposes_core_financial_routes() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    expected_paths = {
        "/contracts/{contract_id}/decisions",
        "/contracts/compile",
        "/verification",
        "/demo/state",
        "/demo/reset",
        "/demo/replay",
    }

    assert expected_paths.issubset(paths)


def test_validation_error_uses_normalized_error_envelope() -> None:
    response = client.post(
        "/contracts/compile",
        json={},
    )

    assert response.status_code == 422

    body = response.json()

    assert body["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    assert "details" in body["error"]
    assert response.headers.get("X-Correlation-ID")


def test_unconfigured_cors_origin_is_rejected() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
