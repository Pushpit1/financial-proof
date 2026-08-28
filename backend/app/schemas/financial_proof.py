"""API schemas for financial proof resources."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


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


class FinancialProofAggregateResponse(BaseModel):
    """Complete financial proof aggregate response."""

    proof: FinancialProofResponse
    claims: list[FinancialClaimResponse]
    evidence: list[EvidenceResponse]
    evidence_links: list[EvidenceLinkResponse]
