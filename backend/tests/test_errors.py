from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors.domain import (
    ConflictError,
    DomainError,
    InfrastructureError,
    NotFoundError,
    PolicyViolationError,
    ValidationDomainError,
)


def create_test_app() -> FastAPI:
    app = FastAPI()

    from app.api.exception_handlers import domain_error_handler  # noqa: I001

    app.add_exception_handler(DomainError, domain_error_handler)

    @app.get("/domain")
    async def domain_error() -> None:
        raise DomainError(
            "Domain error",
            details={"reason": "test"},
        )

    @app.get("/validation")
    async def validation_error() -> None:
        raise ValidationDomainError(
            "Validation failed",
            details={"field": "amount"},
        )

    @app.get("/not-found")
    async def not_found_error() -> None:
        raise NotFoundError("Resource not found")

    @app.get("/conflict")
    async def conflict_error() -> None:
        raise ConflictError("Operation conflicts with current state")

    @app.get("/policy")
    async def policy_error() -> None:
        raise PolicyViolationError("Operation violates policy")

    @app.get("/infrastructure")
    async def infrastructure_error() -> None:
        raise InfrastructureError("Infrastructure dependency failed")

    return app


client = TestClient(create_test_app())


def test_domain_error_handler() -> None:
    response = client.get("/domain")

    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "error": {
            "code": "DOMAIN_ERROR",
            "message": "Domain error",
            "details": {"reason": "test"},
        },
    }


def test_validation_domain_error_handler() -> None:
    response = client.get("/validation")

    assert response.status_code == 422
    assert response.json() == {
        "success": False,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Validation failed",
            "details": {"field": "amount"},
        },
    }


def test_not_found_error_handler() -> None:
    response = client.get("/not-found")

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "error": {
            "code": "NOT_FOUND",
            "message": "Resource not found",
            "details": {},
        },
    }


def test_conflict_error_handler() -> None:
    response = client.get("/conflict")

    assert response.status_code == 409
    assert response.json() == {
        "success": False,
        "error": {
            "code": "CONFLICT",
            "message": "Operation conflicts with current state",
            "details": {},
        },
    }


def test_policy_violation_error_handler() -> None:
    response = client.get("/policy")

    assert response.status_code == 403
    assert response.json() == {
        "success": False,
        "error": {
            "code": "POLICY_VIOLATION",
            "message": "Operation violates policy",
            "details": {},
        },
    }


def test_infrastructure_error_handler() -> None:
    response = client.get("/infrastructure")

    assert response.status_code == 503
    assert response.json() == {
        "success": False,
        "error": {
            "code": "INFRASTRUCTURE_ERROR",
            "message": "Infrastructure dependency failed",
            "details": {},
        },
    }