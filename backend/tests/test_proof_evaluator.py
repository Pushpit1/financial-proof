from decimal import Decimal

from app.domain.enums.financial import (
    ClaimType,
    ProofStatus,
    VerificationStatus,
)
from app.domain.models.financial import FinancialClaim, FinancialProof
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

def test_low_confidence_requires_review() -> None:
    claims = [
        make_claim("0.60"),
        make_claim("0.50"),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.NEEDS_REVIEW
    assert result.overall_confidence.value == Decimal("0.55")


def test_confidence_at_threshold_is_ready() -> None:
    claims = [
        make_claim("0.70"),
        make_claim("0.70"),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.READY
    assert result.overall_confidence.value == Decimal("0.70")


def test_low_confidence_does_not_override_contradiction() -> None:
    claims = [
        make_claim("0.40"),
        make_claim(
            "0.30",
            VerificationStatus.CONTRADICTED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.INVALID

def test_mixed_verified_and_unverified_requires_review() -> None:
    claims = [
        make_claim(
            "0.95",
            VerificationStatus.VERIFIED,
        ),
        make_claim(
            "0.90",
            VerificationStatus.UNVERIFIED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.NEEDS_REVIEW
    assert result.overall_confidence.value == Decimal("0.925")


def test_mixed_verified_and_partially_supported_requires_review() -> None:
    claims = [
        make_claim(
            "0.95",
            VerificationStatus.VERIFIED,
        ),
        make_claim(
            "0.85",
            VerificationStatus.PARTIALLY_SUPPORTED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.NEEDS_REVIEW
    assert result.overall_confidence.value == Decimal("0.90")


def test_supported_claims_with_low_average_require_review() -> None:
    claims = [
        make_claim(
            "0.60",
            VerificationStatus.SUPPORTED,
        ),
        make_claim(
            "0.50",
            VerificationStatus.SUPPORTED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.NEEDS_REVIEW
    assert result.overall_confidence.value == Decimal("0.55")


def test_verified_claims_with_high_average_are_ready() -> None:
    claims = [
        make_claim(
            "0.70",
            VerificationStatus.VERIFIED,
        ),
        make_claim(
            "0.90",
            VerificationStatus.VERIFIED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.READY
    assert result.overall_confidence.value == Decimal("0.80")


def test_contradiction_wins_over_partial_support() -> None:
    claims = [
        make_claim(
            "0.95",
            VerificationStatus.PARTIALLY_SUPPORTED,
        ),
        make_claim(
            "0.95",
            VerificationStatus.CONTRADICTED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.INVALID
    assert result.overall_confidence.value == Decimal("0.95")


def test_contradiction_wins_over_unverified_claim() -> None:
    claims = [
        make_claim(
            "1.00",
            VerificationStatus.UNVERIFIED,
        ),
        make_claim(
            "1.00",
            VerificationStatus.CONTRADICTED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.INVALID

def test_apply_evaluation_updates_status_and_confidence() -> None:
    proof = FinancialProof(subject="Applicant")

    evaluation = ProofEvaluator().evaluate(
        [
            make_claim("0.90"),
            make_claim("0.70"),
        ]
    )

    proof.apply_evaluation(evaluation)

    assert proof.status == ProofStatus.READY
    assert proof.overall_confidence.value == Decimal("0.80")


def test_apply_evaluation_does_not_change_proof_identity() -> None:
    proof = FinancialProof(subject="Applicant")
    proof_id = proof.id

    evaluation = ProofEvaluator().evaluate(
        [
            make_claim("0.90"),
        ]
    )

    proof.apply_evaluation(evaluation)

    assert proof.id == proof_id
    assert proof.subject == "Applicant"

