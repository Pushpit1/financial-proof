"""Tests for financial proof domain services."""

from decimal import Decimal

from app.domain.enums.financial import (
    ClaimType,
    ConfidenceLevel,
    ProofStatus,
    VerificationStatus,
)
from app.domain.models.financial import FinancialClaim, FinancialProof
from app.domain.services.financial import FinancialProofService
from app.domain.value_objects.financial import ConfidenceScore


def make_claim(
    confidence: str,
    status: VerificationStatus = VerificationStatus.UNVERIFIED,
) -> FinancialClaim:
    """Create a test financial claim."""
    return FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject="monthly salary",
        confidence=ConfidenceScore(Decimal(confidence)),
        verification_status=status,
    )


def test_empty_claims_have_zero_confidence() -> None:
    result = FinancialProofService.calculate_overall_confidence([])

    assert result == Decimal("0")


def test_calculate_overall_confidence() -> None:
    claims = [
        make_claim("0.8"),
        make_claim("0.6"),
        make_claim("1.0"),
    ]

    result = FinancialProofService.calculate_overall_confidence(claims)

    assert result == Decimal("0.8")


def test_very_low_confidence_level() -> None:
    result = FinancialProofService.determine_confidence_level(
        Decimal("0.19")
    )

    assert result == ConfidenceLevel.VERY_LOW


def test_low_confidence_level() -> None:
    result = FinancialProofService.determine_confidence_level(
        Decimal("0.39")
    )

    assert result == ConfidenceLevel.LOW


def test_medium_confidence_level() -> None:
    result = FinancialProofService.determine_confidence_level(
        Decimal("0.59")
    )

    assert result == ConfidenceLevel.MEDIUM


def test_high_confidence_level() -> None:
    result = FinancialProofService.determine_confidence_level(
        Decimal("0.79")
    )

    assert result == ConfidenceLevel.HIGH


def test_very_high_confidence_level() -> None:
    result = FinancialProofService.determine_confidence_level(
        Decimal("0.80")
    )

    assert result == ConfidenceLevel.VERY_HIGH


def test_empty_proof_requires_review() -> None:
    proof = FinancialProof(subject="Applicant")

    result = FinancialProofService.evaluate_proof(proof, [])

    assert result.status == ProofStatus.NEEDS_REVIEW
    assert result.overall_confidence.value == Decimal("0")


def test_verified_claims_make_proof_ready() -> None:
    proof = FinancialProof(subject="Applicant")

    claims = [
        make_claim("0.9", VerificationStatus.VERIFIED),
        make_claim("0.8", VerificationStatus.VERIFIED),
    ]

    result = FinancialProofService.evaluate_proof(proof, claims)

    assert result.status == ProofStatus.READY
    assert result.overall_confidence.value == Decimal("0.85")


def test_unverified_claims_require_review() -> None:
    proof = FinancialProof(subject="Applicant")

    claims = [
        make_claim("0.9", VerificationStatus.VERIFIED),
        make_claim("0.7", VerificationStatus.SUPPORTED),
    ]

    result = FinancialProofService.evaluate_proof(proof, claims)

    assert result.status == ProofStatus.NEEDS_REVIEW


def test_contradicted_claim_invalidates_proof() -> None:
    proof = FinancialProof(subject="Applicant")

    claims = [
        make_claim("0.9", VerificationStatus.VERIFIED),
        make_claim("0.2", VerificationStatus.CONTRADICTED),
    ]

    result = FinancialProofService.evaluate_proof(proof, claims)

    assert result.status == ProofStatus.INVALID
