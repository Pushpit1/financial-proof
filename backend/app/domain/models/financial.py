from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from app.domain.enums.financial import (
    ClaimType,
    ConfidenceLevel,
    ContractIdempotencyMode,
    EvidenceStatus,
    EvidenceType,
    ProofStatus,
    VerificationStatus,
)
from app.domain.value_objects.financial import (
    ConfidenceScore,
    ContractAuthorization,
    ContractField,
    ContractIdempotencyPolicy,
    ContractRule,
    ContractStateTransition,
    ContractTemporalRule,
    FinancialConstraint,
    FinancialPeriod,
    Money,
)

if TYPE_CHECKING:
    from app.domain.services.proof_evaluator import ProofEvaluation


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
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


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

    inputs: tuple[ContractField, ...] = field(default_factory=tuple)
    outputs: tuple[ContractField, ...] = field(default_factory=tuple)

    financial_constraints: tuple[FinancialConstraint, ...] = field(
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

    authorizations: tuple[ContractAuthorization, ...] = field(
        default_factory=tuple
    )
    temporal_rules: tuple[ContractTemporalRule, ...] = field(
        default_factory=tuple
    )
    idempotency_policy: ContractIdempotencyPolicy | None = None
    state_transitions: tuple[ContractStateTransition, ...] = field(
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

        self._validate_unique_fields()
        self._validate_unique_rules()
        self._validate_unique_constraints()
        self._validate_idempotency_reference()
        self._validate_unique_state_transitions()

    def _validate_unique_fields(self) -> None:
        input_names = [field.name for field in self.inputs]
        output_names = [field.name for field in self.outputs]

        if len(input_names) != len(set(input_names)):
            raise ValueError(
                "Duplicate contract input field names are not allowed."
            )

        if len(output_names) != len(set(output_names)):
            raise ValueError(
                "Duplicate contract output field names are not allowed."
            )

    def _validate_unique_rules(self) -> None:
        rules = (
            *self.preconditions,
            *self.invariants,
            *self.postconditions,
        )

        names = [rule.name for rule in rules]

        if len(names) != len(set(names)):
            raise ValueError(
                "Duplicate contract rule names are not allowed."
            )

    def _validate_unique_constraints(self) -> None:
        fields = [
            constraint.field
            for constraint in self.financial_constraints
        ]

        if len(fields) != len(set(fields)):
            raise ValueError(
                "Duplicate financial constraints are not allowed."
            )

        declared_fields = {
            contract_field.name
            for contract_field in self.inputs
        }

        for constraint in self.financial_constraints:
            if constraint.field not in declared_fields:
                raise ValueError(
                    "Financial constraint field must reference "
                    "a declared contract field."
                )

    def _validate_unique_authorizations(self) -> None:
        keys = [
            (
                authorization.actor,
                authorization.action,
                authorization.resource,
            )
            for authorization in self.authorizations
        ]

        if len(keys) != len(set(keys)):
            raise ValueError(
                "Duplicate contract authorizations are not allowed."
            )

    def _validate_idempotency_reference(self) -> None:
        if self.idempotency_policy is None:
            return

        if self.idempotency_policy.mode == ContractIdempotencyMode.DISABLED:
            return

        input_names = {
            contract_field.name
            for contract_field in self.inputs
        }

        key_field = self.idempotency_policy.key_field

        if key_field is not None and key_field not in input_names:
            raise ValueError(
                "Idempotency key field must reference "
                "a declared contract field."
            )

    def _validate_unique_state_transitions(self) -> None:
        keys = [
            (
                transition.from_state,
                transition.to_state,
                transition.trigger,
            )
            for transition in self.state_transitions
        ]

        if len(keys) != len(set(keys)):
            raise ValueError(
                "Duplicate contract state transition."
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


@dataclass(frozen=True)
class FinancialContractDecision:
    """Immutable persisted decision produced by contract evaluation."""

    contract_id: UUID
    passed: bool
    reason_codes: tuple[str, ...] = ()
    violation_count: int = 0
    evaluated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.violation_count < 0:
            raise ValueError(
                "Decision violation count cannot be negative."
            )

        if self.violation_count != len(self.reason_codes):
            raise ValueError(
                "Decision violation count must match reason codes."
            )



