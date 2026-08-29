from dataclasses import dataclass
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
    """Business rules controlling financial proof evaluation."""

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

        if self.minimum_review_confidence > self.minimum_ready_confidence:
            raise ValueError(
                "Minimum review confidence cannot exceed "
                "minimum ready confidence."
            )

        if not (
            Decimal("0")
            <= self.minimum_supported_claim_ratio
            <= Decimal("1")
        ):
            raise ValueError(
                "Minimum supported claim ratio must be between 0 and 1."
            )


@dataclass(frozen=True)
class ProofEvaluation:
    """Result produced by evaluating financial proof claims."""

    status: ProofStatus
    overall_confidence: ConfidenceScore
    reasons: tuple[EvaluationReason, ...]


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
        """Determine proof status, confidence, and reasons."""

        overall_confidence = self._calculate_overall_confidence(
            claims
        )

        status, reasons = self._determine_status_and_reasons(
            claims,
            overall_confidence,
        )

        return ProofEvaluation(
            status=status,
            overall_confidence=overall_confidence,
            reasons=reasons,
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

    @staticmethod
    def _calculate_supported_claim_ratio(
        claims: list[FinancialClaim],
    ) -> Decimal:
        """Calculate the ratio of claims with support."""

        if not claims:
            return Decimal("1")

        supported_count = sum(
            claim.verification_status
            in {
                VerificationStatus.SUPPORTED,
                VerificationStatus.VERIFIED,
            }
            for claim in claims
        )

        return Decimal(supported_count) / Decimal(len(claims))

    def _determine_status_and_reasons(
        self,
        claims: list[FinancialClaim],
        overall_confidence: ConfidenceScore,
    ) -> tuple[
        ProofStatus,
        tuple[EvaluationReason, ...],
    ]:
        """Determine proof status and deterministic explanations."""

        if not claims:
            return (
                ProofStatus.READY,
                (EvaluationReason.NO_CLAIMS,),
            )

        if any(
            claim.verification_status
            == VerificationStatus.CONTRADICTED
            for claim in claims
        ):
            return (
                ProofStatus.INVALID,
                (EvaluationReason.CONTRADICTED_CLAIM,),
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

        if reasons:
            return (
                ProofStatus.NEEDS_REVIEW,
                tuple(reasons),
            )

        return (
            ProofStatus.READY,
            (EvaluationReason.EVALUATION_PASSED,),
        )
