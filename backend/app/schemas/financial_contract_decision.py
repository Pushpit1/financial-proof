"""Schemas for financial contract decision evaluation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FinancialContractDecisionEvaluateRequest(BaseModel):
    """Request context for evaluating a financial contract."""

    context: dict[str, object] = Field(default_factory=dict)


class FinancialContractDecisionResponse(BaseModel):
    """Persisted financial contract decision response."""

    id: UUID
    contract_id: UUID
    passed: bool
    reason_codes: list[str]
    violation_count: int
    evaluated_at: datetime
