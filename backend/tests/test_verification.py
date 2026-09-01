from app.domain.models.verification_snapshot import VerificationSnapshot
from app.domain.services.verification import VerificationService
from app.domain.services.verification_comparison import (
    VerificationComparisonService,
)


def test_verification_passes_without_regression() -> None:
    before = VerificationSnapshot(
        contract_version="1",
        system_version="1",
        violations=("refund_without_approval",),
    )

    after = VerificationSnapshot(
        contract_version="1",
        system_version="1",
        violations=(),
    )

    comparison = VerificationComparisonService.compare(
        before,
        after,
    )

    result = VerificationService.verify(comparison)

    assert result.passed is True
    assert result.regression_detected is False
    assert result.violations == ()


def test_verification_fails_when_new_violation_is_introduced() -> None:
    before = VerificationSnapshot(
        contract_version="1",
        system_version="1",
        violations=(),
    )

    after = VerificationSnapshot(
        contract_version="1",
        system_version="1",
        violations=("duplicate_charge",),
    )

    comparison = VerificationComparisonService.compare(
        before,
        after,
    )

    result = VerificationService.verify(comparison)

    assert result.passed is False
    assert result.regression_detected is True
    assert result.violations == ("duplicate_charge",)


def test_verification_preserves_comparison_identity() -> None:
    before = VerificationSnapshot(
        contract_version="1",
        system_version="1",
    )

    after = VerificationSnapshot(
        contract_version="1",
        system_version="1",
    )

    comparison = VerificationComparisonService.compare(
        before,
        after,
    )

    result = VerificationService.verify(comparison)

    assert result.before_snapshot_id == comparison.before_snapshot_id
    assert result.after_snapshot_id == comparison.after_snapshot_id
    assert result.comparison_id == comparison.comparison_id


def test_verification_is_immutable() -> None:
    before = VerificationSnapshot(
        contract_version="1",
        system_version="1",
    )

    after = VerificationSnapshot(
        contract_version="1",
        system_version="1",
    )

    comparison = VerificationComparisonService.compare(
        before,
        after,
    )

    result = VerificationService.verify(comparison)

    try:
        result.passed = False
    except Exception as exc:
        assert "frozen" in str(exc).lower()
    else:
        raise AssertionError("Verification result must be immutable.")
