from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.logging import get_logger, log_event
from app.db.session import get_db
from app.schemas.common import HealthResponse, ReadinessResponse

router = APIRouter(tags=["system"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ReadinessResponse,
            "description": "Database is unavailable.",
        }
    },
)
async def ready(
    db: Session = Depends(get_db),  # noqa: B008
) -> ReadinessResponse | JSONResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        log_event(
            logger,
            "database_readiness_failed",
            fields={"error_type": type(exc).__name__},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ReadinessResponse(status="unready").model_dump(),
        )

    return ReadinessResponse(status="ready")