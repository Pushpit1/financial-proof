"""API router aggregation."""

from fastapi import APIRouter

from app.api.routes.financial_contract import (
    router as financial_contract_router,
)
from app.api.routes.financial_contract_decision import (
    router as financial_contract_decision_router,
)
from app.api.routes.financial_proof import (
    router as financial_proof_router,
)
from app.api.routes.razorpay_webhook import router as razorpay_webhook_router

api_router = APIRouter()


@api_router.get("/health")
async def health() -> dict[str, str]:
    """Return application health status."""
    return {"status": "ok"}


@api_router.get("/ready")
async def ready() -> dict[str, str]:
    """Return application readiness status."""
    return {"status": "ready"}


api_router.include_router(financial_proof_router)
api_router.include_router(financial_contract_decision_router)
api_router.include_router(financial_contract_router)
api_router.include_router(razorpay_webhook_router)

