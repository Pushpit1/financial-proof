from dataclasses import dataclass
from decimal import Decimal

from app.domain.enums.financial import (
    ProofStatus,
    VerificationStatus,
)
from app.domain.models.financial import FinancialClaim
from app.domain.value_objects.financial import ConfidenceScore


@dataclass(frozen=True)
class ProofEvaluation:
    """Result produced by evaluating financial proof claims."""

    status: ProofStatus
    overall_confidence: ConfidenceScore


class ProofEvaluator:
    """Evaluate financial proof state from domain claims."""

    def evaluate(
        self,
        claims: list[FinancialClaim],
    ) -> ProofEvaluation:
        """Determine proof status and aggregate confidence."""

        if not claims:
            return ProofEvaluation(
                status=ProofStatus.READY,
                overall_confidence=ConfidenceScore(
                    Decimal("0")
                ),
            )

        confidence_values = [
            claim.confidence.value
            for claim in claims
        ]

        overall_confidence = (
            sum(confidence_values)
            / Decimal(len(confidence_values))
        )

        has_contradiction = any(
            claim.verification_status
            == VerificationStatus.CONTRADICTED
            for claim in claims
        )

        requires_review = any(
            claim.verification_status
            in {
                VerificationStatus.UNVERIFIED,
                VerificationStatus.PARTIALLY_SUPPORTED,
            }
            for claim in claims
        )

        if has_contradiction:
            status = ProofStatus.INVALID
        elif requires_review:
            status = ProofStatus.NEEDS_REVIEW
        else:
            status = ProofStatus.READY

        return ProofEvaluation(
            status=status,
            overall_confidence=ConfidenceScore(
                overall_confidence
            ),
        )
