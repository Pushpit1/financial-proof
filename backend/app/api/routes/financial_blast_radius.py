"""Financial blast-radius analysis API routes."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_financial_contract_service
from app.application.services.deterministic_contract_compiler import (
    DeterministicFinancialContractCompiler,
)
from app.application.services.financial_contract import (
    FinancialContractApplicationService,
)
from app.db.repositories.financial_blast_radius import (
    SqlAlchemyFinancialBlastRadiusRepository,
)
from app.db.session import get_db
from app.domain.enums.financial import ContractOperator
from app.domain.models.financial import FinancialContract
from app.domain.services.contract_evaluator import ContractEvaluator
from app.domain.services.financial_blast_radius import (
    FinancialBlastRadiusAnalyzer,
)
from app.domain.value_objects.financial import (
    ContractField,
    ContractSourceText,
    FinancialConstraint,
)

router = APIRouter(prefix="/blast-radius", tags=["financial-blast-radius"])


class BlastRadiusAnalyzeRequest(BaseModel):
    contract_id: UUID | None = None
    source_text: str | None = None
    payment_amount: Decimal = Field(..., gt=Decimal("0"))
    refund_amount: Decimal = Field(..., ge=Decimal("0"))
    currency: str = Field(default="INR", min_length=3, max_length=3)
    persist: bool = False


class ExposureResponse(BaseModel):
    id: UUID
    source_violation_id: UUID | None
    field: str | None
    amount: str
    currency: str | None
    explanation: str
    direct_loss: str
    duplicate_charge_exposure: str
    duplicate_fulfillment_exposure: str
    refund_exposure: str
    unauthorized_action_exposure: str
    actual_exposure: str
    maximum_exposure: str


class BlastRadiusResponse(BaseModel):
    analysis_id: UUID
    persisted: bool
    passed: bool
    violation_count: int
    total_direct_loss: str
    total_actual_exposure: str
    total_maximum_exposure: str
    currency: str
    exposures: list[ExposureResponse]


def _serialize_analysis(
    analysis,
    *,
    persisted: bool,
    passed: bool,
    violation_count: int,
    currency: str,
) -> BlastRadiusResponse:
    total_direct = sum(
        (exp.direct_loss for exp in analysis.exposures),
        Decimal("0"),
    )
    total_actual = sum(
        (exp.actual_exposure for exp in analysis.exposures),
        Decimal("0"),
    )
    total_max = sum(
        (exp.maximum_exposure for exp in analysis.exposures),
        Decimal("0"),
    )
    return BlastRadiusResponse(
        analysis_id=analysis.analysis_id,
        persisted=persisted,
        passed=passed,
        violation_count=violation_count,
        total_direct_loss=str(total_direct),
        total_actual_exposure=str(total_actual),
        total_maximum_exposure=str(total_max),
        currency=currency,
        exposures=[
            ExposureResponse(
                id=exp.analysis_id,
                source_violation_id=exp.source_violation_id,
                field=exp.field,
                amount=str(exp.amount),
                currency=exp.currency,
                explanation=exp.explanation,
                direct_loss=str(exp.direct_loss),
                duplicate_charge_exposure=str(exp.duplicate_charge_exposure),
                duplicate_fulfillment_exposure=str(
                    exp.duplicate_fulfillment_exposure
                ),
                refund_exposure=str(exp.refund_exposure),
                unauthorized_action_exposure=str(
                    exp.unauthorized_action_exposure
                ),
                actual_exposure=str(exp.actual_exposure),
                maximum_exposure=str(exp.maximum_exposure),
            )
            for exp in analysis.exposures
        ],
    )


@router.post("", response_model=BlastRadiusResponse, status_code=status.HTTP_200_OK)
async def analyze_blast_radius(
    request: BlastRadiusAnalyzeRequest,
    db: Session = Depends(get_db),  # noqa: B008
    contract_service: FinancialContractApplicationService = Depends(  # noqa: B008
        get_financial_contract_service
    ),
) -> BlastRadiusResponse:
    """Deterministically evaluate financial constraints and compute blast radius."""
    currency = request.currency.upper()
    contract: FinancialContract | None = None

    if request.contract_id is not None:
        contract = contract_service.get_contract(request.contract_id)
        if contract is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Financial contract {request.contract_id} was not found.",
            )
    elif request.source_text:
        compiler = DeterministicFinancialContractCompiler()
        contract = compiler.compile(ContractSourceText(request.source_text)).contract
    else:
        contract = FinancialContract(
            name="Refund ceiling rule",
            version=1,
            inputs=(
                ContractField(name="payment_amount", data_type="decimal"),
                ContractField(name="refund_amount", data_type="decimal"),
            ),
            financial_constraints=(
                FinancialConstraint(
                    field="refund_amount",
                    operator=ContractOperator.LESS_THAN_OR_EQUAL,
                    value=request.payment_amount,
                    currency=currency,
                ),
            ),
        )

    if not contract.financial_constraints:
        existing_inputs = list(contract.inputs)
        existing_names = {f.name for f in existing_inputs}
        if "payment_amount" not in existing_names:
            existing_inputs.append(
                ContractField(name="payment_amount", data_type="decimal")
            )
        if "refund_amount" not in existing_names:
            existing_inputs.append(
                ContractField(name="refund_amount", data_type="decimal")
            )
        contract = FinancialContract(
            id=contract.id,
            name=contract.name,
            version=contract.version,
            minimum_confidence=contract.minimum_confidence,
            minimum_supported_claim_ratio=contract.minimum_supported_claim_ratio,
            required_claim_types=contract.required_claim_types,
            inputs=tuple(existing_inputs),
            financial_constraints=(
                FinancialConstraint(
                    field="refund_amount",
                    operator=ContractOperator.LESS_THAN_OR_EQUAL,
                    value=request.payment_amount,
                    currency=currency,
                ),
            ),
        )

    context = {
        "payment_amount": request.payment_amount,
        "refund_amount": request.refund_amount,
    }
    evaluation = ContractEvaluator().evaluate(contract, context)
    analysis = FinancialBlastRadiusAnalyzer.analyze(contract, evaluation, context)

    persisted = False
    if request.persist:
        repo = SqlAlchemyFinancialBlastRadiusRepository(db)
        repo.save(analysis)
        db.commit()
        persisted = True

    return _serialize_analysis(
        analysis,
        persisted=persisted,
        passed=evaluation.passed,
        violation_count=len(evaluation.violations),
        currency=currency,
    )


@router.get("", response_model=list[BlastRadiusResponse])
async def list_blast_radius(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),  # noqa: B008
) -> list[BlastRadiusResponse]:
    """List persisted blast-radius analyses."""
    repo = SqlAlchemyFinancialBlastRadiusRepository(db)
    analyses = repo.list_all(limit=limit, offset=offset)
    return [
        _serialize_analysis(
            analysis,
            persisted=True,
            passed=len(analysis.exposures) == 0,
            violation_count=len(analysis.exposures),
            currency=(
                analysis.exposures[0].currency or "INR"
                if analysis.exposures
                else "INR"
            ),
        )
        for analysis in analyses
    ]


@router.get("/{analysis_id}", response_model=BlastRadiusResponse)
async def get_blast_radius(
    analysis_id: UUID,
    db: Session = Depends(get_db),  # noqa: B008
) -> BlastRadiusResponse:
    """Retrieve one persisted blast-radius analysis by ID."""
    repo = SqlAlchemyFinancialBlastRadiusRepository(db)
    analysis = repo.get_by_id(analysis_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blast radius analysis {analysis_id} was not found.",
        )
    return _serialize_analysis(
        analysis,
        persisted=True,
        passed=len(analysis.exposures) == 0,
        violation_count=len(analysis.exposures),
        currency=(
            analysis.exposures[0].currency or "INR"
            if analysis.exposures
            else "INR"
        ),
    )
