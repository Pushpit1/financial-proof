"""Aggregate API router."""

from fastapi import APIRouter

from app.api.routes.demo import router as demo_router
from app.api.routes.financial_contract import router as financial_contract_router
from app.api.routes.financial_contract_compiler import (
    router as financial_contract_compiler_router,
)
from app.api.routes.financial_contract_decision import (
    router as financial_contract_decision_router,
)
from app.api.routes.financial_proof import router as financial_proof_router
from app.api.routes.financial_simulation import (
    router as financial_simulation_router,
)
from app.api.routes.health import router as health_router
from app.api.routes.razorpay_webhook import router as razorpay_webhook_router
from app.api.routes.verification import router as verification_router

api_router = APIRouter()

api_router.include_router(health_router)

# More-specific nested routes must be registered before
# generic /contracts/{name}/{version} routes.
api_router.include_router(financial_contract_decision_router)

api_router.include_router(financial_contract_router)
api_router.include_router(financial_contract_compiler_router)
api_router.include_router(financial_proof_router)
api_router.include_router(financial_simulation_router)
api_router.include_router(verification_router)
api_router.include_router(razorpay_webhook_router)
api_router.include_router(demo_router)
