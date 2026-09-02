"""Centralized API exception handlers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors.domain import DomainError
from app.schemas.common import ErrorDetail, ErrorResponse


def _correlation_id(request: Request) -> str | None:
    """Return the correlation ID attached by middleware, when available."""
    value = getattr(request.state, "correlation_id", None)
    return str(value) if value else None


def _json_safe(value: Any) -> Any:
    """Convert validation details into JSON-safe primitive values."""
    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, BaseException):
        return str(value)

    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]

    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=str)]

    return value


def _response_headers(request: Request) -> dict[str, str]:
    """Build response headers containing the correlation ID when available."""
    correlation_id = _correlation_id(request)
    if correlation_id:
        return {"X-Correlation-ID": correlation_id}
    return {}


async def domain_error_handler(
    request: Request,
    exc: DomainError,
) -> JSONResponse:
    """Convert an expected domain failure into the public error contract."""
    response = ErrorResponse(
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            details=_json_safe(exc.details),
        )
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(),
        headers=_response_headers(request),
    )


async def request_validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return safe, structured request-validation failures."""
    response = ErrorResponse(
        error=ErrorDetail(
            code="REQUEST_VALIDATION_ERROR",
            message="Request validation failed.",
            details={
                "errors": _json_safe(exc.errors()),
            },
        )
    )

    return JSONResponse(
        status_code=422,
        content=response.model_dump(),
        headers=_response_headers(request),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a safe generic response for unexpected application failures."""
    response = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal error occurred.",
            details={},
        )
    )

    return JSONResponse(
        status_code=500,
        content=response.model_dump(),
        headers=_response_headers(request),
    )
