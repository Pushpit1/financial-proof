"""Domain service for evaluating financial proof quality."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.enums.financial import (
    EvaluationReason,
    ProofStatus,
    VerificationStatus,
)
from app.domain.models.financial import FinancialClaim
from app.domain.value_objects.financial import ConfidenceScore


@dataclass(frozen=True)
class ProofEvaluationPolicy:
    """Configuration governing financial proof evaluation."""

    minimum_review_confidence: Decimal = Decimal("0.00")
    minimum_ready_confidence: Decimal = Decimal("0.70")
    minimum_supported_claim_ratio: Decimal = Decimal("1.00")

    def __post_init__(self) -> None:
        """Validate evaluation confidence thresholds."""
        if not isinstance(self.minimum_review_confidence, Decimal):
            raise TypeError(
                "Minimum review confidence must be a Decimal."
            )

        if not isinstance(self.minimum_ready_confidence, Decimal):
            raise TypeError(
                "Minimum ready confidence must be a Decimal."
            )

        if not isinstance(
            self.minimum_supported_claim_ratio,
            Decimal,
        ):
            raise TypeError(
                "Minimum supported claim ratio must be a Decimal."
            )

        if not (
            Decimal("0")
            <= self.minimum_review_confidence
            <= Decimal("1")
        ):
            raise ValueError(
                "Minimum review confidence must be between 0 and 1."
            )

        if not (
            Decimal("0")
            <= self.minimum_ready_confidence
            <= Decimal("1")
        ):
            raise ValueError(
                "Minimum ready confidence must be between 0 and 1."
            )

        if not (
            Decimal("0")
            <= self.minimum_supported_claim_ratio
            <= Decimal("1")
        ):
            raise ValueError(
                "Minimum supported claim ratio must be between 0 and 1."
            )

        if self.minimum_review_confidence > self.minimum_ready_confidence:
            raise ValueError(
                "Minimum review confidence cannot exceed "
                "minimum ready confidence."
            )


@dataclass(frozen=True)
class ProofEvaluation:
    """Immutable result produced by proof evaluation."""

    status: ProofStatus
    overall_confidence: ConfidenceScore
    reasons: tuple[EvaluationReason, ...] = field(default_factory=tuple)


class ProofEvaluator:
    """Evaluate a collection of financial claims."""

    def __init__(
        self,
        policy: ProofEvaluationPolicy | None = None,
    ) -> None:
        self.policy = policy or ProofEvaluationPolicy()

    def evaluate(
        self,
        claims: Sequence[FinancialClaim],
    ) -> ProofEvaluation:
        """Evaluate claims and return an immutable evaluation result."""
        if not claims:
            return ProofEvaluation(
                status=ProofStatus.READY,
                overall_confidence=ConfidenceScore(Decimal("0")),
                reasons=(EvaluationReason.NO_CLAIMS,),
            )

        overall_confidence = self._calculate_overall_confidence(
            claims
        )

        if any(
            claim.verification_status
            == VerificationStatus.CONTRADICTED
            for claim in claims
        ):
            return ProofEvaluation(
                status=ProofStatus.INVALID,
                overall_confidence=overall_confidence,
                reasons=(EvaluationReason.CONTRADICTED_CLAIM,),
            )

        reasons: list[EvaluationReason] = []

        if any(
            claim.verification_status
            == VerificationStatus.UNVERIFIED
            for claim in claims
        ):
            reasons.append(EvaluationReason.UNVERIFIED_CLAIM)

        if any(
            claim.verification_status
            == VerificationStatus.PARTIALLY_SUPPORTED
            for claim in claims
        ):
            reasons.append(
                EvaluationReason.PARTIALLY_SUPPORTED_CLAIM
            )

        if (
            overall_confidence.value
            < self.policy.minimum_review_confidence
        ):
            reasons.append(
                EvaluationReason.CONFIDENCE_BELOW_REVIEW_THRESHOLD
            )

        if (
            overall_confidence.value
            < self.policy.minimum_ready_confidence
        ):
            reasons.append(
                EvaluationReason.CONFIDENCE_BELOW_READY_THRESHOLD
            )

        supported_claim_ratio = self._calculate_supported_claim_ratio(
            claims
        )

        if (
            supported_claim_ratio
            < self.policy.minimum_supported_claim_ratio
        ):
            reasons.append(
                EvaluationReason.SUPPORTED_CLAIM_RATIO_BELOW_THRESHOLD
            )

        if not reasons:
            reasons.append(EvaluationReason.EVALUATION_PASSED)
            status = ProofStatus.READY
        elif (
            EvaluationReason.CONFIDENCE_BELOW_REVIEW_THRESHOLD
            in reasons
        ):
            status = ProofStatus.NEEDS_REVIEW
        else:
            status = ProofStatus.NEEDS_REVIEW

        return ProofEvaluation(
            status=status,
            overall_confidence=overall_confidence,
            reasons=tuple(reasons),
        )

    @staticmethod
    def _calculate_overall_confidence(
        claims: Sequence[FinancialClaim],
    ) -> ConfidenceScore:
        """Calculate average claim confidence."""
        total = sum(
            (claim.confidence.value for claim in claims),
            Decimal("0"),
        )
        average = total / Decimal(len(claims))
        return ConfidenceScore(average)

    @staticmethod
    def _calculate_supported_claim_ratio(
        claims: Sequence[FinancialClaim],
    ) -> Decimal:
        """Calculate the ratio of fully supported claims."""
        supported_count = sum(
            claim.verification_status
            in {
                VerificationStatus.VERIFIED,
                VerificationStatus.SUPPORTED,
            }
            for claim in claims
        )

        return Decimal(supported_count) / Decimal(len(claims))


