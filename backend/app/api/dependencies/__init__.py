"""Dependency providers for API routes."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.ports.payment_gateway import PaymentGatewayPort
from app.application.ports.unit_of_work import FinancialUnitOfWorkPort
from app.application.ports.webhook_replay import (
    InMemoryWebhookReplayStore,
    WebhookReplayStore,
)
from app.application.services.deterministic_contract_compiler import (
    DeterministicFinancialContractCompiler,
)
from app.application.services.financial_contract import (
    FinancialContractApplicationService,
)
from app.application.services.financial_contract_compiler import (
    FinancialContractCompilerService,
)
from app.application.services.financial_proof import (
    FinancialProofApplicationService,
)
from app.application.services.razorpay_webhook import RazorpayWebhookService
from app.core.config import get_settings
from app.db.session import get_db
from app.db.unit_of_work import FinancialUnitOfWork
from app.domain.services.proof_evaluator import (
    ProofEvaluationPolicy,
    ProofEvaluator,
)
from app.infrastructure.razorpay_adapter import RazorpayPaymentGateway
from app.infrastructure.razorpay_settings import RazorpaySettings

_webhook_replay_store = InMemoryWebhookReplayStore()


def get_financial_unit_of_work(
    db: Annotated[Session, Depends(get_db)],
) -> FinancialUnitOfWorkPort:
    """Build the application unit-of-work boundary."""
    return FinancialUnitOfWork(db)


def get_financial_proof_service(
    unit_of_work: Annotated[
        FinancialUnitOfWorkPort,
        Depends(get_financial_unit_of_work),
    ],
) -> FinancialProofApplicationService:
    """Build the financial proof application service."""
    settings = get_settings()

    policy = ProofEvaluationPolicy(
        minimum_review_confidence=settings.proof_minimum_review_confidence,
        minimum_ready_confidence=settings.proof_minimum_ready_confidence,
        minimum_supported_claim_ratio=(
            settings.proof_minimum_supported_claim_ratio
        ),
    )

    return FinancialProofApplicationService(
        unit_of_work,
        evaluator=ProofEvaluator(policy),
    )


def get_financial_contract_service(
    unit_of_work: Annotated[
        FinancialUnitOfWorkPort,
        Depends(get_financial_unit_of_work),
    ],
) -> FinancialContractApplicationService:
    """Build the financial contract application service."""
    return FinancialContractApplicationService(
        unit_of_work,
    )


def get_financial_contract_compiler_service() -> FinancialContractCompilerService:
    """Build the natural-language financial contract compiler service."""
    return FinancialContractCompilerService(
        compiler=DeterministicFinancialContractCompiler(),
    )


def get_razorpay_settings() -> RazorpaySettings:
    """Build Razorpay infrastructure settings from environment configuration."""
    return RazorpaySettings()


def get_razorpay_gateway() -> PaymentGatewayPort:
    """Build the Razorpay payment gateway at the infrastructure boundary."""
    return RazorpayPaymentGateway(
        settings=get_razorpay_settings(),
    )


def get_razorpay_webhook_replay_store() -> WebhookReplayStore:
    """Build the shared webhook replay store."""
    return _webhook_replay_store


def get_razorpay_webhook_service(
    gateway: Annotated[
        PaymentGatewayPort,
        Depends(get_razorpay_gateway),
    ],
    replay_store: Annotated[
        WebhookReplayStore,
        Depends(get_razorpay_webhook_replay_store),
    ],
) -> RazorpayWebhookService:
    """Build the Razorpay webhook application service."""
    return RazorpayWebhookService(
        gateway,
        replay_store,
    )


__all__ = [
    "get_financial_contract_compiler_service",
    "get_financial_contract_service",
    "get_financial_proof_service",
    "get_financial_unit_of_work",
    "get_razorpay_gateway",
    "get_razorpay_settings",
    "get_razorpay_webhook_replay_store",
    "get_razorpay_webhook_service",
]
