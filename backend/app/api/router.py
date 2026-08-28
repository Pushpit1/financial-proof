from fastapi import APIRouter

from app.api.routes.financial_proof import (
    router as financial_proof_router,
)
from app.api.routes.health import router as health_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(financial_proof_router)
