from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from app.domain.enums.financial import (
    ClaimType,
    ConfidenceLevel,
    EvidenceStatus,
    EvidenceType,
    ProofStatus,
    VerificationStatus,
)

if TYPE_CHECKING:
    from app.domain.services.proof_evaluator import ProofEvaluation

from app.domain.value_objects.financial import (
    ConfidenceScore,
    FinancialPeriod,
    Money,
)


@dataclass
class Evidence:
    """
    A source artifact from which financial facts can be established.
    """

    evidence_type: EvidenceType
    source_name: str
    received_at: date
    id: UUID = field(default_factory=uuid4)
    status: EvidenceStatus = EvidenceStatus.RECEIVED
    checksum: str | None = None
    source_reference: str | None = None


@dataclass
class FinancialClaim:
    """
    A normalized financial assertion derived from one or more evidence items.
    """

    claim_type: ClaimType
    subject: str
    period: FinancialPeriod | None = None
    amount: Money | None = None
    id: UUID = field(default_factory=uuid4)
    verification_status: VerificationStatus = (
        VerificationStatus.UNVERIFIED
    )
    confidence: ConfidenceScore = field(
        default_factory=lambda: ConfidenceScore(Decimal("0"))
    )
    confidence_level: ConfidenceLevel = ConfidenceLevel.VERY_LOW


@dataclass
class EvidenceLink:
    """
    Links a claim to evidence supporting or contradicting it.
    """

    claim_id: UUID
    evidence_id: UUID
    id: UUID = field(default_factory=uuid4)
    verification_status: VerificationStatus = (
        VerificationStatus.UNVERIFIED
    )
    confidence: ConfidenceScore = field(
        default_factory=lambda: ConfidenceScore(Decimal("0"))
    )
    explanation: str | None = None


@dataclass
class FinancialProof:
    """
    A defensible collection of claims and supporting evidence.
    """

    subject: str
    id: UUID = field(default_factory=uuid4)
    status: ProofStatus = ProofStatus.DRAFT
    claim_ids: list[UUID] = field(default_factory=list)
    evidence_ids: list[UUID] = field(default_factory=list)
    overall_confidence: ConfidenceScore = field(
        default_factory=lambda: ConfidenceScore(Decimal("0"))
    )
    def apply_evaluation(
        self,
        evaluation: 'ProofEvaluation',
    ) -> None:
        """Apply an evaluation result to this proof."""
        self.status = evaluation.status
        self.overall_confidence = evaluation.overall_confidence

