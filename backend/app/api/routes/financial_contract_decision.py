"""Financial contract decision API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_financial_contract_service
from app.api.dependencies.financial_contract_decision import (
    get_financial_contract_decision_service,
)
from app.application.services.financial_contract import (
    FinancialContractApplicationService,
)
from app.application.services.financial_contract_decision import (
    FinancialContractDecisionService,
)
from app.schemas.financial_contract_decision import (
    FinancialContractDecisionEvaluateRequest,
    FinancialContractDecisionResponse,
)

router = APIRouter(
    prefix="/contracts",
    tags=["financial-contract-decision"],
)


def _decision_to_response(decision) -> FinancialContractDecisionResponse:
    """Convert a domain decision into an API response."""
    return FinancialContractDecisionResponse(
        id=decision.id,
        contract_id=decision.contract_id,
        passed=decision.passed,
        reason_codes=list(decision.reason_codes),
        violation_count=decision.violation_count,
        evaluated_at=decision.evaluated_at,
    )


@router.post(
    "/{contract_id}/decisions",
    response_model=FinancialContractDecisionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def evaluate_contract(
    contract_id: UUID,
    request: FinancialContractDecisionEvaluateRequest,
    contract_service: FinancialContractApplicationService = Depends(  # noqa: B008
        get_financial_contract_service
    ),
    decision_service: FinancialContractDecisionService = Depends(  # noqa: B008
        get_financial_contract_decision_service
    ),
) -> FinancialContractDecisionResponse:
    """Evaluate and persist a financial contract decision."""
    contract = contract_service.get_contract(contract_id)

    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial contract {contract_id} was not found.",
        )

    try:
        decision = decision_service.evaluate(
            contract,
            request.context,
            persist=True,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return _decision_to_response(decision)


@router.get(
    "/{contract_id}/decisions",
    response_model=list[FinancialContractDecisionResponse],
    status_code=status.HTTP_200_OK,
)
async def list_contract_decisions(
    contract_id: UUID,
    contract_service: FinancialContractApplicationService = Depends(  # noqa: B008
        get_financial_contract_service
    ),
    decision_service: FinancialContractDecisionService = Depends(  # noqa: B008
        get_financial_contract_decision_service
    ),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[FinancialContractDecisionResponse]:
    """Return a page of persisted decisions for a financial contract."""
    contract = contract_service.get_contract(contract_id)

    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial contract {contract_id} was not found.",
        )

    try:
        decisions = decision_service.list_decisions(
            contract_id,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return [
        _decision_to_response(decision)
        for decision in decisions
    ]

