import pytest
from pydantic import ValidationError

from app.schemas.common import (
    APIResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    ReadinessResponse,
)


def test_api_response() -> None:
    response = APIResponse[str](data="ok")

    assert response.success is True
    assert response.data == "ok"


def test_error_response() -> None:
    response = ErrorResponse(
        error=ErrorDetail(
            code="TEST_ERROR",
            message="Test error",
        )
    )

    assert response.success is False
    assert response.error.code == "TEST_ERROR"


def test_health_response() -> None:
    response = HealthResponse(status="ok")

    assert response.status == "ok"


def test_readiness_response() -> None:
    response = ReadinessResponse(status="ready")

    assert response.status == "ready"


def test_error_code_cannot_be_empty() -> None:
    with pytest.raises(ValidationError):
        ErrorDetail(
            code="",
            message="Invalid",
        )