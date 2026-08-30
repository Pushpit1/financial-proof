from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from app.domain.enums.financial import (
    ClaimType,
    ConfidenceLevel,
    ContractRuleType,
    EvidenceStatus,
    EvidenceType,
    ProofStatus,
    VerificationStatus,
)

if TYPE_CHECKING:
    from app.domain.services.proof_evaluator import ProofEvaluation

from app.domain.value_objects.financial import (
    ConfidenceScore,
    ContractRule,
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
    A normalized financial assertion derived from one or more evidence
    items.
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
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


@dataclass(frozen=True)
class ProofEvaluationHistory:
    """Immutable persisted record of a financial proof evaluation."""

    id: UUID
    proof_id: UUID
    status: ProofStatus
    overall_confidence: ConfidenceScore
    evaluation_reasons: tuple[str, ...]
    evaluated_at: datetime


@dataclass(frozen=True)
class FinancialContract:
    """Immutable contract defining rules for financial proof decisions."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    version: int = 1
    minimum_confidence: ConfidenceScore = field(
        default_factory=lambda: ConfidenceScore(Decimal("0"))
    )
    minimum_supported_claim_ratio: Decimal = Decimal("1")
    required_claim_types: tuple[ClaimType, ...] = field(
        default_factory=tuple
    )
    preconditions: tuple[ContractRule, ...] = field(
        default_factory=tuple
    )
    invariants: tuple[ContractRule, ...] = field(
        default_factory=tuple
    )
    postconditions: tuple[ContractRule, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        """Validate contract invariants."""
        if not self.name.strip():
            raise ValueError("Contract name cannot be empty.")

        if self.version < 1:
            raise ValueError("Contract version must be at least 1.")

        if not (
            Decimal("0")
            <= self.minimum_supported_claim_ratio
            <= Decimal("1")
        ):
            raise ValueError(
                "Minimum supported claim ratio must be between 0 and 1."
            )

        self._validate_rule_types(
            self.preconditions,
            ContractRuleType.PRECONDITION,
        )
        self._validate_rule_types(
            self.invariants,
            ContractRuleType.INVARIANT,
        )
        self._validate_rule_types(
            self.postconditions,
            ContractRuleType.POSTCONDITION,
        )

    @staticmethod
    def _validate_rule_types(
        rules: tuple[ContractRule, ...],
        expected_type: ContractRuleType,
    ) -> None:
        for rule in rules:
            if rule.rule_type != expected_type:
                raise ValueError(
                    "Contract rule must have type "
                    f"'{expected_type.value}'."
                )


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
    evaluation_reasons: list[str] = field(default_factory=list)

    def apply_evaluation(
        self,
        evaluation: "ProofEvaluation",
    ) -> None:
        """Apply an evaluation result to this proof."""
        self.status = evaluation.status
        self.overall_confidence = evaluation.overall_confidence
        self.evaluation_reasons = list(evaluation.reasons)
