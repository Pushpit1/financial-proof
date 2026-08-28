"""Financial proof domain services."""

from decimal import Decimal

from app.domain.enums.financial import (
    ConfidenceLevel,
    ProofStatus,
    VerificationStatus,
)
from app.domain.models.financial import FinancialClaim, FinancialProof


class FinancialProofService:
    """Business rules for evaluating financial proofs."""

    @staticmethod
    def calculate_overall_confidence(
        claims: list[FinancialClaim],
    ) -> Decimal:
        """Calculate the average confidence across financial claims."""
        if not claims:
            return Decimal("0")

        total = sum(
            (claim.confidence.value for claim in claims),
            Decimal("0"),
        )

        return total / Decimal(len(claims))

    @staticmethod
    def determine_confidence_level(
        confidence: Decimal,
    ) -> ConfidenceLevel:
        """Convert a confidence score into a confidence level."""
        if confidence < Decimal("0.2"):
            return ConfidenceLevel.VERY_LOW

        if confidence < Decimal("0.4"):
            return ConfidenceLevel.LOW

        if confidence < Decimal("0.6"):
            return ConfidenceLevel.MEDIUM

        if confidence < Decimal("0.8"):
            return ConfidenceLevel.HIGH

        return ConfidenceLevel.VERY_HIGH

    @staticmethod
    def evaluate_proof(
        proof: FinancialProof,
        claims: list[FinancialClaim],
    ) -> FinancialProof:
        """Evaluate a proof and update its confidence and status."""
        confidence = FinancialProofService.calculate_overall_confidence(claims)

        proof.overall_confidence = type(proof.overall_confidence)(confidence)

        if not claims:
            proof.status = ProofStatus.NEEDS_REVIEW
            return proof

        all_verified = all(
            claim.verification_status == VerificationStatus.VERIFIED
            for claim in claims
        )

        any_contradicted = any(
            claim.verification_status == VerificationStatus.CONTRADICTED
            for claim in claims
        )

        if any_contradicted:
            proof.status = ProofStatus.INVALID
        elif all_verified:
            proof.status = ProofStatus.READY
        else:
            proof.status = ProofStatus.NEEDS_REVIEW

        return proof
