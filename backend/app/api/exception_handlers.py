from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.errors.domain import DomainError
from app.schemas.common import ErrorDetail, ErrorResponse


async def domain_error_handler(
    request: Request,
    exc: DomainError,
) -> JSONResponse:
    response = ErrorResponse(
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(),
    )