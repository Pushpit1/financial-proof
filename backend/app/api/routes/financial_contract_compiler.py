"""Financial contract compiler API routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_financial_contract_compiler_service
from app.application.services.financial_contract_compiler import (
    FinancialContractCompilerService,
)
from app.domain.models.financial import FinancialContract
from app.domain.value_objects.financial import ContractSourceText
from app.schemas.financial_contract_compiler import (
    FinancialContractCompileContractResponse,
    FinancialContractCompileRequest,
    FinancialContractCompileResponse,
)

router = APIRouter(
    prefix="/contracts",
    tags=["financial-contract-compiler"],
)


def _contract_to_response(
    contract: FinancialContract,
) -> FinancialContractCompileContractResponse:
    """Convert a compiled domain contract into an API response."""
    return FinancialContractCompileContractResponse(
        id=contract.id,
        name=contract.name,
        version=contract.version,
        minimum_confidence=contract.minimum_confidence.value,
        minimum_supported_claim_ratio=(
            contract.minimum_supported_claim_ratio
        ),
        required_claim_types=[
            claim_type.value
            for claim_type in contract.required_claim_types
        ],
    )


@router.post(
    "/compile",
    response_model=FinancialContractCompileResponse,
    status_code=status.HTTP_200_OK,
)
async def compile_contract(
    request: FinancialContractCompileRequest,
    service: FinancialContractCompilerService = Depends(  # noqa: B008
        get_financial_contract_compiler_service,
    ),
) -> FinancialContractCompileResponse:
    """Compile and validate natural-language financial contract text."""
    try:
        result = service.compile(
            ContractSourceText(request.source_text),
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return FinancialContractCompileResponse(
        source_text=result.source_text.normalized(),
        contract=_contract_to_response(result.contract),
    )
