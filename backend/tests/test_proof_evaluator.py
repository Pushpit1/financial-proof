from decimal import Decimal

from app.domain.enums.financial import (
    ClaimType,
    ProofStatus,
    VerificationStatus,
)
from app.domain.models.financial import FinancialClaim, FinancialProof
from app.domain.services.proof_evaluator import (
    ProofEvaluationPolicy,
    ProofEvaluator,
)
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


def test_supported_and_verified_claims_are_ready() -> None:
    claims = [
        make_claim(
            "0.80",
            VerificationStatus.SUPPORTED,
        ),
        make_claim(
            "0.90",
            VerificationStatus.VERIFIED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.READY


def test_unverified_claim_takes_review_priority() -> None:
    claims = [
        make_claim(
            "0.90",
            VerificationStatus.VERIFIED,
        ),
        make_claim(
            "0.80",
            VerificationStatus.UNVERIFIED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.NEEDS_REVIEW


def test_partially_supported_claim_takes_review_priority() -> None:
    claims = [
        make_claim(
            "0.90",
            VerificationStatus.VERIFIED,
        ),
        make_claim(
            "0.80",
            VerificationStatus.PARTIALLY_SUPPORTED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.NEEDS_REVIEW


def test_contradiction_overrides_review() -> None:
    claims = [
        make_claim(
            "0.90",
            VerificationStatus.UNVERIFIED,
        ),
        make_claim(
            "0.80",
            VerificationStatus.PARTIALLY_SUPPORTED,
        ),
        make_claim(
            "0.70",
            VerificationStatus.CONTRADICTED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.INVALID


def test_evaluation_preserves_average_when_status_changes() -> None:
    claims = [
        make_claim(
            "0.90",
            VerificationStatus.VERIFIED,
        ),
        make_claim(
            "0.60",
            VerificationStatus.UNVERIFIED,
        ),
    ]

    result = ProofEvaluator().evaluate(claims)

    assert result.status == ProofStatus.NEEDS_REVIEW
    assert result.overall_confidence.value == Decimal("0.75")


def test_evaluation_is_deterministic() -> None:
    claims = [
        make_claim(
            "0.90",
            VerificationStatus.SUPPORTED,
        ),
        make_claim(
            "0.70",
            VerificationStatus.VERIFIED,
        ),
    ]

    evaluator = ProofEvaluator()

    first = evaluator.evaluate(claims)
    second = evaluator.evaluate(claims)

    assert first == second

def test_default_policy_requires_70_percent_confidence() -> None:
    policy = ProofEvaluationPolicy()

    assert policy.minimum_ready_confidence == Decimal("0.70")


def test_custom_policy_changes_ready_threshold() -> None:
    evaluator = ProofEvaluator(
        ProofEvaluationPolicy(
            minimum_ready_confidence=Decimal("0.80")
        )
    )

    result = evaluator.evaluate(
        [
            make_claim(
                "0.75",
                VerificationStatus.VERIFIED,
            ),
            make_claim(
                "0.75",
                VerificationStatus.VERIFIED,
            ),
        ]
    )

    assert result.status == ProofStatus.NEEDS_REVIEW


def test_custom_policy_allows_higher_confidence() -> None:
    evaluator = ProofEvaluator(
        ProofEvaluationPolicy(
            minimum_ready_confidence=Decimal("0.80")
        )
    )

    result = evaluator.evaluate(
        [
            make_claim(
                "0.85",
                VerificationStatus.VERIFIED,
            ),
            make_claim(
                "0.95",
                VerificationStatus.VERIFIED,
            ),
        ]
    )

    assert result.status == ProofStatus.READY


def test_contradiction_still_overrides_custom_policy() -> None:
    evaluator = ProofEvaluator(
        ProofEvaluationPolicy(
            minimum_ready_confidence=Decimal("0.99")
        )
    )

    result = evaluator.evaluate(
        [
            make_claim(
                "1.00",
                VerificationStatus.CONTRADICTED,
            ),
        ]
    )

    assert result.status == ProofStatus.INVALID


def test_policy_rejects_negative_threshold() -> None:
    try:
        ProofEvaluationPolicy(
            minimum_ready_confidence=Decimal("-0.01")
        )
    except ValueError as exc:
        assert str(exc) == (
            "Minimum ready confidence must be between 0 and 1."
        )
    else:
        raise AssertionError("Expected ValueError")


def test_policy_rejects_threshold_above_one() -> None:
    try:
        ProofEvaluationPolicy(
            minimum_ready_confidence=Decimal("1.01")
        )
    except ValueError as exc:
        assert str(exc) == (
            "Minimum ready confidence must be between 0 and 1."
        )
    else:
        raise AssertionError("Expected ValueError")


def test_policy_accepts_zero_threshold() -> None:
    policy = ProofEvaluationPolicy(
        minimum_ready_confidence=Decimal("0")
    )

    assert policy.minimum_ready_confidence == Decimal("0")


def test_policy_accepts_one_threshold() -> None:
    policy = ProofEvaluationPolicy(
        minimum_ready_confidence=Decimal("1")
    )

    assert policy.minimum_ready_confidence == Decimal("1")


def test_policy_rejects_non_decimal_threshold() -> None:
    try:
        ProofEvaluationPolicy(
            minimum_ready_confidence=0.70,
        )
    except TypeError as exc:
        assert str(exc) == "Minimum ready confidence must be a Decimal."
    else:
        raise AssertionError(
            "Expected TypeError for non-Decimal threshold."
        )

def test_default_policy_has_zero_review_threshold() -> None:
    policy = ProofEvaluationPolicy()

    assert policy.minimum_review_confidence == Decimal("0")

def test_policy_rejects_review_threshold_above_ready() -> None:
    try:
        ProofEvaluationPolicy(
            minimum_review_confidence=Decimal("0.80"),
            minimum_ready_confidence=Decimal("0.70"),
        )
    except ValueError as exc:
        assert str(exc) == (
            "Minimum review confidence cannot exceed "
            "minimum ready confidence."
        )
    else:
        raise AssertionError(
            "Expected ValueError for invalid policy thresholds."
        )

def test_policy_accepts_equal_review_and_ready_thresholds() -> None:
    policy = ProofEvaluationPolicy(
        minimum_review_confidence=Decimal("0.70"),
        minimum_ready_confidence=Decimal("0.70"),
    )

    assert policy.minimum_review_confidence == Decimal("0.70")
    assert policy.minimum_ready_confidence == Decimal("0.70")

def test_confidence_below_review_threshold_requires_review() -> None:
    evaluator = ProofEvaluator(
        ProofEvaluationPolicy(
            minimum_review_confidence=Decimal("0.50"),
            minimum_ready_confidence=Decimal("0.70"),
        )
    )

    result = evaluator.evaluate(
        [
            make_claim("0.40"),
        ]
    )

    assert result.status == ProofStatus.NEEDS_REVIEW

def test_confidence_between_review_and_ready_requires_review() -> None:
    evaluator = ProofEvaluator(
        ProofEvaluationPolicy(
            minimum_review_confidence=Decimal("0.50"),
            minimum_ready_confidence=Decimal("0.70"),
        )
    )

    result = evaluator.evaluate(
        [
            make_claim("0.60"),
        ]
    )

    assert result.status == ProofStatus.NEEDS_REVIEW

def test_default_policy_requires_all_claims_supported() -> None:
    policy = ProofEvaluationPolicy()

    assert policy.minimum_supported_claim_ratio == Decimal("1.00")

def test_supported_claim_ratio_can_require_review() -> None:
    evaluator = ProofEvaluator(
        ProofEvaluationPolicy(
            minimum_ready_confidence=Decimal("0.70"),
            minimum_supported_claim_ratio=Decimal("1.00"),
        )
    )

    result = evaluator.evaluate(
        [
            make_claim(
                "0.90",
                VerificationStatus.SUPPORTED,
            ),
            make_claim(
                "0.90",
                VerificationStatus.UNVERIFIED,
            ),
        ]
    )

    assert result.status == ProofStatus.NEEDS_REVIEW

def test_supported_claim_ratio_accepts_fully_supported_claims() -> None:
    evaluator = ProofEvaluator(
        ProofEvaluationPolicy(
            minimum_ready_confidence=Decimal("0.70"),
            minimum_supported_claim_ratio=Decimal("1.00"),
        )
    )

    result = evaluator.evaluate(
        [
            make_claim(
                "0.80",
                VerificationStatus.SUPPORTED,
            ),
            make_claim(
                "0.90",
                VerificationStatus.VERIFIED,
            ),
        ]
    )

    assert result.status == ProofStatus.READY

def test_policy_rejects_invalid_supported_claim_ratio() -> None:
    try:
        ProofEvaluationPolicy(
            minimum_supported_claim_ratio=Decimal("1.01"),
        )
    except ValueError as exc:
        assert str(exc) == (
            "Minimum supported claim ratio must be between 0 and 1."
        )
    else:
        raise AssertionError(
            "Expected ValueError for invalid supported claim ratio."
        )
