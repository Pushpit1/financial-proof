from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.metrics import get_metrics_registry
from app.db.session import get_db
from app.schemas.common import HealthResponse, ReadinessResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadinessResponse)
async def ready(
    db: Session = Depends(get_db),  # noqa: B008
) -> ReadinessResponse:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable.",
        ) from exc

    return ReadinessResponse(status="ready")


@router.get("/system/status")
async def system_status(
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, object]:
    """Return safe, non-secret runtime diagnostics and deterministic metrics."""
    cfg = get_settings()
    db_status = "connected"
    db_error: str | None = None
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = "unreachable"
        db_error = type(exc).__name__

    return {
        "app": cfg.app_name,
        "version": cfg.app_version,
        "environment": cfg.app_env,
        "database": db_status,
        "database_error_type": db_error,
        "auth_configured": cfg.api_auth_token is not None,
        "metrics": get_metrics_registry().snapshot(),
    }
