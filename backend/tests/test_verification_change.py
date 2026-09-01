from app.domain.models.verification_snapshot import VerificationSnapshot
from app.domain.services.verification_comparison import (
    VerificationComparisonService,
)


def test_comparison_creates_baseline_change_records() -> None:
    before = VerificationSnapshot(
        contract_version="contract-v1",
        system_version="system-v1",
        baseline={"balance": 1000},
    )

    after = VerificationSnapshot(
        contract_version="contract-v1",
        system_version="system-v1",
        baseline={"balance": 750},
    )

    comparison = VerificationComparisonService.compare(before, after)

    assert len(comparison.changes) == 1

    change = comparison.changes[0]

    assert change.field == "balance"
    assert change.before == 1000
    assert change.after == 750
    assert change.change_type == "baseline_field_changed"


def test_comparison_creates_violation_change_records() -> None:
    before = VerificationSnapshot(
        contract_version="contract-v1",
        system_version="system-v1",
        violations=("refund_without_approval",),
    )

    after = VerificationSnapshot(
        contract_version="contract-v1",
        system_version="system-v1",
        violations=("duplicate_charge",),
    )

    comparison = VerificationComparisonService.compare(before, after)

    assert comparison.resolved_violations == (
        "refund_without_approval",
    )
    assert comparison.introduced_violations == (
        "duplicate_charge",
    )

    assert len(comparison.changes) == 2

    change_types = {
        change.change_type
        for change in comparison.changes
    }

    assert change_types == {
        "violation_resolved",
        "violation_introduced",
    }


def test_change_records_are_deterministically_ordered() -> None:
    before = VerificationSnapshot(
        contract_version="contract-v1",
        system_version="system-v1",
        baseline={
            "z": 1,
            "a": 1,
        },
    )

    after = VerificationSnapshot(
        contract_version="contract-v1",
        system_version="system-v1",
        baseline={
            "z": 2,
            "a": 2,
        },
    )

    comparison = VerificationComparisonService.compare(before, after)

    assert [
        change.field
        for change in comparison.changes
    ] == ["a", "z"]
