"""API schemas for financial contracts."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class FinancialContractCreateRequest(BaseModel):
    """Request body for creating a financial contract."""

    id: UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    version: int = Field(ge=1)
    minimum_confidence: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    minimum_supported_claim_ratio: Decimal = Field(
        ge=Decimal("0"),
        le=Decimal("1"),
    )
    required_claim_types: list[str]


class FinancialContractResponse(BaseModel):
    """API representation of a financial contract."""

    id: UUID
    name: str
    version: int
    minimum_confidence: Decimal
    minimum_supported_claim_ratio: Decimal
    required_claim_types: list[str]