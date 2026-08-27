from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from app.core.errors.domain import (
    ConflictError,
    InfrastructureError,
    NotFoundError,
    PolicyViolationError,
    ValidationDomainError,
)


def create_test_app() -> FastAPI:
    app = FastAPI()
    from app.api.exception_handlers import domain_error_handler

    from app.core.errors.domain import DomainError

    app.add_exception_handler(DomainError, domain_error_handler)

    router = APIRouter()

    @router.get("/not-found")
    async def not_found() -> None:
        raise NotFoundError(
            "Transaction was not found.",
            details={"resource": "transaction"},
        )

    @router.get("/conflict")
    async def conflict() -> None:
        raise ConflictError("Transaction is already finalized.")

    @router.get("/policy")
    async def policy() -> None:
        raise PolicyViolationError("Transaction exceeds policy limit.")

    @router.get("/validation")
    async def validation() -> None:
        raise ValidationDomainError("Invalid transaction amount.")

    @router.get("/infrastructure")
    async def infrastructure() -> None:
        raise InfrastructureError("Payment provider unavailable.")

    app.include_router(router)

    return app


client = TestClient(create_test_app())


def test_not_found_error() -> None:
    response = client.get("/not-found")

    assert response.status_code == 404
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_conflict_error() -> None:
    response = client.get("/conflict")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


def test_policy_violation_error() -> None:
    response = client.get("/policy")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "POLICY_VIOLATION"


def test_validation_error() -> None:
    response = client.get("/validation")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_infrastructure_error() -> None:
    response = client.get("/infrastructure")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "INFRASTRUCTURE_ERROR"