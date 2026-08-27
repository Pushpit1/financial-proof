from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

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
    db.execute(text("SELECT 1"))

    return ReadinessResponse(status="ready")