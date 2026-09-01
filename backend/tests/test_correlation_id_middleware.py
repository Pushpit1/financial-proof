import uuid

import structlog
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.middleware import CorrelationIDMiddleware


def create_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(CorrelationIDMiddleware)

    @app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        context = structlog.contextvars.get_contextvars()

        return {
            "correlation_id": context["correlation_id"],
        }

    return app


def test_preserves_supplied_correlation_id() -> None:
    client = TestClient(create_test_app())

    response = client.get(
        "/test",
        headers={"X-Correlation-ID": "client-correlation-123"},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == (
        "client-correlation-123"
    )
    assert response.json()["correlation_id"] == (
        "client-correlation-123"
    )


def test_generates_correlation_id_when_missing() -> None:
    client = TestClient(create_test_app())

    response = client.get("/test")

    correlation_id = response.headers["X-Correlation-ID"]

    assert response.status_code == 200
    assert correlation_id
    assert response.json()["correlation_id"] == correlation_id

    uuid.UUID(correlation_id)


def test_correlation_context_is_cleared_after_request() -> None:
    structlog.contextvars.clear_contextvars()

    client = TestClient(create_test_app())

    response = client.get(
        "/test",
        headers={"X-Correlation-ID": "request-context-123"},
    )

    assert response.status_code == 200
    assert structlog.contextvars.get_contextvars() == {}
