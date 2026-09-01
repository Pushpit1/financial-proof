from uuid import uuid4

from app.domain.models.verification_snapshot import VerificationSnapshot
from app.domain.services.verification_comparison import (
    VerificationComparisonService,
)


def make_snapshot(
    *,
    contract_version: str = "1",
    system_version: str = "0.1.0",
    baseline: dict | None = None,
    violations: tuple[str, ...] = (),
    counterexample_ids: tuple = (),
) -> VerificationSnapshot:
    return VerificationSnapshot(
        contract_version=contract_version,
        system_version=system_version,
        baseline=baseline or {},
        violations=violations,
        counterexample_ids=counterexample_ids,
    )


def test_identical_snapshots_have_no_changes() -> None:
    snapshot = make_snapshot(
        baseline={"balance": "1000"},
        violations=("none",),
    )

    result = VerificationComparisonService.compare(
        snapshot,
        snapshot,
    )

    assert result.contract_version_changed is False
    assert result.system_version_changed is False
    assert result.added_changes == ()
    assert result.removed_changes == ()
    assert result.introduced_violations == ()
    assert result.resolved_violations == ()
    assert result.regression_detected is False


def test_comparison_detects_version_changes() -> None:
    before = make_snapshot(
        contract_version="1",
        system_version="0.1.0",
    )
    after = make_snapshot(
        contract_version="2",
        system_version="0.2.0",
    )

    result = VerificationComparisonService.compare(
        before,
        after,
    )

    assert result.contract_version_changed is True
    assert result.system_version_changed is True


def test_comparison_detects_violation_regression() -> None:
    before = make_snapshot(
        violations=("duplicate_charge",),
    )
    after = make_snapshot(
        violations=("duplicate_charge", "negative_balance"),
    )

    result = VerificationComparisonService.compare(
        before,
        after,
    )

    assert result.introduced_violations == ("negative_balance",)
    assert result.resolved_violations == ()
    assert result.regression_detected is True


def test_comparison_detects_resolved_violations() -> None:
    before = make_snapshot(
        violations=("duplicate_charge", "invalid_state"),
    )
    after = make_snapshot(
        violations=("invalid_state",),
    )

    result = VerificationComparisonService.compare(
        before,
        after,
    )

    assert result.introduced_violations == ()
    assert result.resolved_violations == ("duplicate_charge",)
    assert result.regression_detected is False


def test_comparison_detects_counterexample_changes() -> None:
    first = uuid4()
    second = uuid4()

    before = make_snapshot(
        counterexample_ids=(first,),
    )
    after = make_snapshot(
        counterexample_ids=(second,),
    )

    result = VerificationComparisonService.compare(
        before,
        after,
    )

    assert result.added_counterexample_ids == (second,)
    assert result.removed_counterexample_ids == (first,)


def test_comparison_is_deterministic() -> None:
    first = uuid4()
    second = uuid4()

    before = make_snapshot(
        baseline={"b": 2, "a": 1},
        violations=("z", "a"),
        counterexample_ids=(second, first),
    )
    after = make_snapshot(
        baseline={"d": 4, "c": 3},
        violations=("z", "b"),
        counterexample_ids=(first,),
    )

    result_one = VerificationComparisonService.compare(before, after)
    result_two = VerificationComparisonService.compare(before, after)

    assert result_one.model_dump(
        exclude={"comparison_id"},
    ) == result_two.model_dump(
        exclude={"comparison_id"},
    )


def test_comparison_is_immutable() -> None:
    before = make_snapshot()
    after = make_snapshot()

    result = VerificationComparisonService.compare(
        before,
        after,
    )

    try:
        result.regression_detected = True
    except Exception as exc:
        assert "frozen" in str(exc).lower()
    else:
        raise AssertionError("Comparison must be immutable.")
