from decimal import Decimal

from app.domain.enums.financial import (
    ClaimType,
    ProofStatus,
    VerificationStatus,
)
from app.domain.models.financial import FinancialClaim
from app.domain.services.proof_evaluator import ProofEvaluator
from app.domain.value_objects.financial import ConfidenceScore


def make_claim(
    confidence: str,
    verification_status: VerificationStatus = (
        VerificationStatus.VERIFIED
    ),
) -> FinancialClaim:
    return FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject="Test claim",
        confidence=ConfidenceScore(Decimal(confidence)),
        verification_status=verification_status,
    )


def test_empty_claims_are_ready_with_zero_confidence() -> None:
    result = ProofEvaluator().evaluate([])

    assert result.status == ProofStatus.READY
    assert result.overall_confidence.value == Decimal("0")


def test_claim_confidence_is_averaged() -> None:
    claims = [
        make_claim("0.90"),
        make_claim("0.70"),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.READY
    assert result.overall_confidence.value == Decimal("0.80")


def test_contradicted_claim_makes_proof_invalid() -> None:
    claims = [
        make_claim("0.90"),
        make_claim(
            "0.80",
            VerificationStatus.CONTRADICTED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.INVALID
    assert result.overall_confidence.value == Decimal("0.85")


def test_unverified_claim_requires_review() -> None:
    claims = [
        make_claim(
            "0.90",
            VerificationStatus.UNVERIFIED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.NEEDS_REVIEW
    assert result.overall_confidence.value == Decimal("0.90")


def test_partially_supported_claim_requires_review() -> None:
    claims = [
        make_claim(
            "0.80",
            VerificationStatus.PARTIALLY_SUPPORTED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.NEEDS_REVIEW
    assert result.overall_confidence.value == Decimal("0.80")


def test_supported_claims_are_ready() -> None:
    claims = [
        make_claim(
            "0.80",
            VerificationStatus.SUPPORTED,
        ),
        make_claim(
            "0.90",
            VerificationStatus.SUPPORTED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.READY
    assert result.overall_confidence.value == Decimal("0.85")


def test_verified_claims_are_ready() -> None:
    claims = [
        make_claim("1.00"),
        make_claim("0.90"),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.READY
    assert result.overall_confidence.value == Decimal("0.95")


def test_contradiction_takes_precedence_over_review() -> None:
    claims = [
        make_claim(
            "0.90",
            VerificationStatus.UNVERIFIED,
        ),
        make_claim(
            "0.80",
            VerificationStatus.CONTRADICTED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.INVALID


def test_evaluation_does_not_modify_claims() -> None:
    claims = [
        make_claim("0.90"),
        make_claim("0.70"),
    ]

    original_statuses = [
        claim.verification_status
        for claim in claims
    ]

    ProofEvaluator().evaluate(claims)

    assert [
        claim.verification_status
        for claim in claims
    ] == original_statuses
