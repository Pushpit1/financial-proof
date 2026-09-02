"""API schemas for natural-language financial contract compilation."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FinancialContractCompileRequest(BaseModel):
    """Request body for compiling a natural-language financial contract."""

    model_config = ConfigDict(extra="forbid")

    source_text: str = Field(min_length=1)


class FinancialContractCompileContractResponse(BaseModel):
    """Compiled financial contract returned by the compiler API."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    version: int
    minimum_confidence: Decimal
    minimum_supported_claim_ratio: Decimal
    required_claim_types: list[str]


class FinancialContractCompileResponse(BaseModel):
    """Result returned after compiling natural-language contract text."""

    model_config = ConfigDict(extra="forbid")

    source_text: str
    contract: FinancialContractCompileContractResponse
