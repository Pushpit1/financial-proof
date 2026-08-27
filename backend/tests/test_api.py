from fastapi.testclient import TestClient


def test_root(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200

    body = response.json()

    assert body["name"] == "Financial Proof"
    assert body["version"] == "0.1.0"


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_correlation_id(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"]


def test_custom_correlation_id(client: TestClient) -> None:
    correlation_id = "fp-test-123"

    response = client.get(
        "/health",
        headers={"X-Correlation-ID": correlation_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == correlation_id
