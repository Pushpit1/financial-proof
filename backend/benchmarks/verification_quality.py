"""Reproducibility and verification detection benchmarks."""

from __future__ import annotations

import json
from pathlib import Path

from app.domain.models.verification_snapshot import VerificationSnapshot
from app.domain.services.verification import VerificationService
from app.domain.services.verification_comparison import (
    VerificationComparisonService,
)
from benchmarks.harness import benchmark

RESULTS_PATH = Path("benchmarks/results")

CLEAN_CASES = (
    (
        (),
        (),
    ),
    (
        ("duplicate_charge",),
        ("duplicate_charge",),
    ),
    (
        ("refund_without_approval",),
        (),
    ),
    (
        ("invalid_state",),
        ("invalid_state",),
    ),
)

REGRESSION_CASES = (
    (
        (),
        ("duplicate_charge",),
    ),
    (
        ("duplicate_charge",),
        ("duplicate_charge", "negative_balance"),
    ),
    (
        (),
        ("refund_without_approval",),
    ),
    (
        ("invalid_state",),
        ("duplicate_charge", "invalid_state"),
    ),
)


def _snapshot(violations: tuple[str, ...]) -> VerificationSnapshot:
    """Build a deterministic verification snapshot."""
    return VerificationSnapshot(
        contract_version="1",
        system_version="1",
        baseline={
            "balance": "1000",
            "currency": "INR",
        },
        violations=violations,
        counterexample_ids=(),
    )


def _compare(
    before_violations: tuple[str, ...],
    after_violations: tuple[str, ...],
):
    """Build a verification comparison from known evidence."""
    return VerificationComparisonService.compare(
        _snapshot(before_violations),
        _snapshot(after_violations),
    )


def _signature(result) -> dict[str, object]:
    """Return deterministic evidence while excluding generated IDs."""
    return result.model_dump(
        exclude={
            "comparison_id",
            "before_snapshot_id",
            "after_snapshot_id",
            "verification_id",
        },
    )


def _measure_detection(
    cases: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...],
) -> tuple[int, int]:
    """Return detected regression count and total regression cases."""
    detected = 0

    for before, after in cases:
        result = VerificationService.verify(
            _compare(before, after),
        )
        if result.regression_detected:
            detected += 1

    return detected, len(cases)


def run_benchmark(
    *,
    case_repetitions: int = 1000,
    reproducibility_repetitions: int = 1000,
    warmups: int = 2,
    iterations: int = 5,
) -> dict[str, object]:
    """Measure detection rate, false positives, and reproducibility."""
    if case_repetitions < 1:
        raise ValueError("case_repetitions must be at least 1.")

    if reproducibility_repetitions < 1:
        raise ValueError(
            "reproducibility_repetitions must be at least 1."
        )

    regression_corpus = REGRESSION_CASES * case_repetitions
    clean_corpus = CLEAN_CASES * case_repetitions

    def operation() -> tuple[int, int]:
        detected, regression_total = _measure_detection(
            regression_corpus,
        )

        false_positives, clean_total = _measure_detection(
            CLEAN_CASES * case_repetitions,
        )

        return detected, false_positives

    performance_result, outputs = benchmark(
        name="verification_detection",
        workload_size=len(regression_corpus) + len(clean_corpus),
        operation=operation,
        warmups=warmups,
        iterations=iterations,
    )

    detected_counts = [output[0] for output in outputs]
    false_positive_counts = [output[1] for output in outputs]

    expected_regressions = len(regression_corpus)
    expected_clean = len(clean_corpus)

    detection_rates = [
        detected / expected_regressions
        for detected in detected_counts
    ]

    false_positive_rates = [
        count / expected_clean
        for count in false_positive_counts
    ]

    deterministic_before = _snapshot(
        ("duplicate_charge", "refund_without_approval"),
    )
    deterministic_after = _snapshot(
        ("duplicate_charge", "negative_balance"),
    )

    reference = VerificationComparisonService.compare(
        deterministic_before,
        deterministic_after,
    )

    reference_signature = reference.model_dump(
        exclude={
            "comparison_id",
            "before_snapshot_id",
            "after_snapshot_id",
        },
    )

    reproducible_count = 0

    for _ in range(reproducibility_repetitions):
        candidate = VerificationComparisonService.compare(
            deterministic_before,
            deterministic_after,
        )

        candidate_signature = candidate.model_dump(
            exclude={
                "comparison_id",
                "before_snapshot_id",
                "after_snapshot_id",
            },
        )

        if candidate_signature == reference_signature:
            reproducible_count += 1

    reproducibility_rate = (
        reproducible_count / reproducibility_repetitions
    )

    payload = {
        "benchmark": performance_result.as_dict(),
        "corpus": {
            "regression_cases": len(regression_corpus),
            "clean_cases": len(clean_corpus),
            "case_repetitions": case_repetitions,
            "reproducibility_repetitions": reproducibility_repetitions,
        },
        "detection": {
            "detected_counts": detected_counts,
            "expected_regressions": expected_regressions,
            "detection_rates": detection_rates,
            "minimum_detection_rate": min(detection_rates),
            "maximum_detection_rate": max(detection_rates),
        },
        "false_positives": {
            "false_positive_counts": false_positive_counts,
            "expected_clean_cases": expected_clean,
            "false_positive_rates": false_positive_rates,
            "minimum_false_positive_rate": min(
                false_positive_rates,
            ),
            "maximum_false_positive_rate": max(
                false_positive_rates,
            ),
        },
        "reproducibility": {
            "reproducible_count": reproducible_count,
            "total_comparisons": reproducibility_repetitions,
            "reproducibility_rate": reproducibility_rate,
        },
    }

    RESULTS_PATH.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_PATH / "verification_quality.json"
    output_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    return payload


if __name__ == "__main__":
    print(
        json.dumps(
            run_benchmark(),
            indent=2,
        )
    )

