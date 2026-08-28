from dataclasses import dataclass
from decimal import Decimal

from app.domain.enums.financial import (
    ProofStatus,
    VerificationStatus,
)
from app.domain.models.financial import FinancialClaim
from app.domain.value_objects.financial import ConfidenceScore


@dataclass(frozen=True)
class ProofEvaluationPolicy:
    """Business rules controlling financial proof evaluation."""

    minimum_ready_confidence: Decimal = Decimal("0.70")

    def __post_init__(self) -> None:
        """Validate the ready-confidence threshold."""
        if not Decimal("0") <= self.minimum_ready_confidence <= Decimal("1"):
            raise ValueError(
                "Minimum ready confidence must be between 0 and 1."
            )


@dataclass(frozen=True)
class ProofEvaluation:
    """Result produced by evaluating financial proof claims."""

    status: ProofStatus
    overall_confidence: ConfidenceScore


class ProofEvaluator:
    """Evaluate financial proof state from domain claims."""

    def __init__(
        self,
        policy: ProofEvaluationPolicy | None = None,
    ) -> None:
        self.policy = policy or ProofEvaluationPolicy()

    def evaluate(
        self,
        claims: list[FinancialClaim],
    ) -> ProofEvaluation:
        """Determine proof status and aggregate confidence."""

        overall_confidence = self._calculate_overall_confidence(
            claims
        )

        status = self._determine_status(
            claims,
            overall_confidence,
        )

        return ProofEvaluation(
            status=status,
            overall_confidence=overall_confidence,
        )

    @staticmethod
    def _calculate_overall_confidence(
        claims: list[FinancialClaim],
    ) -> ConfidenceScore:
        """Calculate average claim confidence."""

        if not claims:
            return ConfidenceScore(Decimal("0"))

        confidence_values = [
            claim.confidence.value
            for claim in claims
        ]

        average = (
            sum(confidence_values)
            / Decimal(len(confidence_values))
        )

        return ConfidenceScore(average)

    def _determine_status(
        self,
        claims: list[FinancialClaim],
        overall_confidence: ConfidenceScore,
    ) -> ProofStatus:
        """Determine proof status from domain evaluation rules."""

        if not claims:
            return ProofStatus.READY

        if any(
            claim.verification_status
            == VerificationStatus.CONTRADICTED
            for claim in claims
        ):
            return ProofStatus.INVALID

        if any(
            claim.verification_status
            in {
                VerificationStatus.UNVERIFIED,
                VerificationStatus.PARTIALLY_SUPPORTED,
            }
            for claim in claims
        ):
            return ProofStatus.NEEDS_REVIEW

        if (
            overall_confidence.value
            < self.policy.minimum_ready_confidence
        ):
            return ProofStatus.NEEDS_REVIEW

        return ProofStatus.READY

