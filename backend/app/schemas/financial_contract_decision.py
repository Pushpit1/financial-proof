"""Schemas for financial contract decision evaluation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FinancialContractDecisionEvaluateRequest(BaseModel):
    """Request context for evaluating a financial contract."""

    model_config = ConfigDict(extra="forbid")

    context: dict[str, object] = Field(
        default_factory=dict,
        max_length=100,
    )


class FinancialContractDecisionResponse(BaseModel):
    """Persisted financial contract decision response."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    contract_id: UUID
    passed: bool
    reason_codes: list[str]
    violation_count: int
    evaluated_at: datetime
