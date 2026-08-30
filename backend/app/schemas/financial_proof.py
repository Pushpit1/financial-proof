"""API schemas for financial proof resources."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.enums.financial import (
    ClaimType,
    ConfidenceLevel,
    EvidenceType,
    VerificationStatus,
)


class FinancialClaimCreateRequest(BaseModel):
    """API input for creating a financial claim."""

    id: UUID | None = None
    claim_type: ClaimType
    subject: str = Field(min_length=1)
    amount: Decimal | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    confidence: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    confidence_level: ConfidenceLevel = ConfidenceLevel.VERY_LOW

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str) -> str:
        """Reject blank claim subjects."""
        if not value.strip():
            raise ValueError("subject must not be blank")
        return value

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        """Normalize supplied currency codes."""
        return value.upper() if value is not None else None

    @model_validator(mode="after")
    def validate_amount_currency(self) -> "FinancialClaimCreateRequest":
        """Require amount and currency to appear together."""
        if self.amount is not None and self.currency is None:
            raise ValueError("currency is required when amount is provided")

        if self.currency is not None and self.amount is None:
            raise ValueError("amount is required when currency is provided")

        return self


class EvidenceCreateRequest(BaseModel):
    """API input for creating evidence."""

    id: UUID | None = None
    evidence_type: EvidenceType
    source_name: str = Field(min_length=1)
    received_at: date
    status: str = "received"
    checksum: str | None = None
    source_reference: str | None = None

    @field_validator("source_name")
    @classmethod
    def validate_source_name(cls, value: str) -> str:
        """Reject blank evidence source names."""
        if not value.strip():
            raise ValueError("source_name must not be blank")
        return value


class EvidenceLinkCreateRequest(BaseModel):
    """API input for creating an evidence link."""

    id: UUID | None = None
    claim_id: UUID
    evidence_id: UUID
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    confidence: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    explanation: str | None = None


class FinancialProofCreateRequest(BaseModel):
    """API input for creating a financial proof."""

    id: UUID | None = None
    subject: str = Field(min_length=1)
    claims: list[FinancialClaimCreateRequest] = Field(default_factory=list)
    evidence: list[EvidenceCreateRequest] = Field(default_factory=list)
    evidence_links: list[EvidenceLinkCreateRequest] = Field(
        default_factory=list
    )

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str) -> str:
        """Reject blank proof subjects."""
        if not value.strip():
            raise ValueError("subject must not be blank")
        return value


class FinancialClaimResponse(BaseModel):
    """API representation of a financial claim."""

    id: UUID
    claim_type: str
    subject: str
    amount: Decimal | None
    currency: str | None
    verification_status: str
    confidence: Decimal
    confidence_level: str


class EvidenceResponse(BaseModel):
    """API representation of evidence."""

    id: UUID
    evidence_type: str
    source_name: str
    received_at: date
    status: str
    checksum: str | None
    source_reference: str | None


class EvidenceLinkResponse(BaseModel):
    """API representation of an evidence link."""

    id: UUID
    claim_id: UUID
    evidence_id: UUID
    verification_status: str
    confidence: Decimal
    explanation: str | None


class FinancialProofResponse(BaseModel):
    """API representation of a financial proof."""

    id: UUID
    subject: str
    status: str
    overall_confidence: Decimal
    evaluation_reasons: list[str] = Field(default_factory=list)


class FinancialProofAggregateResponse(BaseModel):
    """Complete financial proof aggregate response."""

    proof: FinancialProofResponse
    claims: list[FinancialClaimResponse]
    evidence: list[EvidenceResponse]
    evidence_links: list[EvidenceLinkResponse]


class ProofEvaluationResponse(BaseModel):
    """API representation of a persisted proof evaluation."""

    id: UUID
    proof_id: UUID
    status: str
    overall_confidence: Decimal
    evaluation_reasons: list[str] = Field(default_factory=list)
    evaluated_at: datetime
