"""Tests for centralized API error handling."""

from fastapi import APIRouter
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.core.errors.domain import DomainError
from app.main import create_app


def _build_test_app():
    app = create_app()
    app.debug = False
    router = APIRouter()

    @router.get("/test-errors/unexpected")
    async def test_unexpected():
        raise RuntimeError("SECRET_INTERNAL_FAILURE")

    @router.get("/test-errors/{value}")
    async def test_validation(value: int):
        return {"value": value}

    app.include_router(router)
    return app


def test_request_validation_error_is_structured_and_safe():
    client = TestClient(_build_test_app())

    response = client.get("/test-errors/not-an-integer")

    assert response.status_code == 422
    assert response.json() == {
        "success": False,
        "error": {
            "code": "REQUEST_VALIDATION_ERROR",
            "message": "Request validation failed.",
            "details": {
                "errors": [
                    {
                        "type": "int_parsing",
                        "loc": ["path", "value"],
                        "msg": (
                            "Input should be a valid integer, unable to "
                            "parse string as an integer"
                        ),
                        "input": "not-an-integer",
                    }
                ]
            },
        }
    }
    assert response.headers["X-Correlation-ID"]


def test_unexpected_exception_is_structured_and_does_not_leak_details():
    client = TestClient(_build_test_app(), raise_server_exceptions=False)

    response = client.get("/test-errors/unexpected")

    assert response.status_code == 500
    body = response.json()

    assert body == {
        "success": False,
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected internal error occurred.",
            "details": {},
        }
    }
    assert "SECRET_INTERNAL_FAILURE" not in response.text
    assert response.headers["X-Correlation-ID"]


def test_domain_error_handler_remains_registered():
    app = create_app()

    handlers = app.exception_handlers

    assert DomainError in handlers
    assert RequestValidationError in handlers
    assert Exception in handlers
