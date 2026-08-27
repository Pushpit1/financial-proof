from fastapi import APIRouter

from app.schemas.common import HealthResponse, ReadinessResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadinessResponse)
async def ready() -> ReadinessResponse:
    return ReadinessResponse(status="ready")