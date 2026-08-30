"""Financial contract API routes."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_financial_contract_service
from app.application.services.financial_contract import (
    FinancialContractApplicationService,
)
from app.domain.enums.financial import ClaimType
from app.domain.models.financial import FinancialContract
from app.domain.value_objects.financial import ConfidenceScore
from app.schemas.financial_contract import (
    FinancialContractCreateRequest,
    FinancialContractResponse,
)

router = APIRouter(
    prefix="/contracts",
    tags=["financial-contract"],
)


def _contract_to_response(
    contract: FinancialContract,
) -> FinancialContractResponse:
    """Convert a domain contract into an API response."""
    return FinancialContractResponse(
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


def _request_to_domain(
    request: FinancialContractCreateRequest,
) -> FinancialContract:
    """Convert an API request into a domain contract."""
    try:
        required_claim_types = tuple(
            ClaimType(claim_type)
            for claim_type in request.required_claim_types
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid claim type in required_claim_types.",
        ) from exc

    return FinancialContract(
        id=request.id or uuid4(),
        name=request.name,
        version=request.version,
        minimum_confidence=ConfidenceScore(
            request.minimum_confidence
        ),
        minimum_supported_claim_ratio=(
            request.minimum_supported_claim_ratio
        ),
        required_claim_types=required_claim_types,
    )


@router.post(
    "",
    response_model=FinancialContractResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_contract(
    request: FinancialContractCreateRequest,
    service: FinancialContractApplicationService = Depends(  # noqa: B008
        get_financial_contract_service
    ),
) -> FinancialContractResponse:
    """Create and persist a financial contract."""
    contract = _request_to_domain(request)

    try:
        created = service.create_contract(contract)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return _contract_to_response(created)


@router.get(
    "/{contract_id}",
    response_model=FinancialContractResponse,
)
async def get_contract(
    contract_id: UUID,
    service: FinancialContractApplicationService = Depends(  # noqa: B008
        get_financial_contract_service
    ),
) -> FinancialContractResponse:
    """Return a financial contract by ID."""
    contract = service.get_contract(contract_id)

    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial contract {contract_id} was not found.",
        )

    return _contract_to_response(contract)


@router.get(
    "/{name}/{version}",
    response_model=FinancialContractResponse,
)
async def get_contract_version(
    name: str,
    version: int,
    service: FinancialContractApplicationService = Depends(  # noqa: B008
        get_financial_contract_service
    ),
) -> FinancialContractResponse:
    """Return a specific financial contract version."""
    contract = service.get_contract_version(name, version)

    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Financial contract '{name}' version "
                f"{version} was not found."
            ),
        )

    return _contract_to_response(contract)