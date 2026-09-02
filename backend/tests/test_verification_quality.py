from benchmarks.verification_quality import (
    run_benchmark,
)


def test_quality_benchmark_rejects_invalid_case_repetitions() -> None:
    try:
        run_benchmark(
            case_repetitions=0,
            reproducibility_repetitions=1,
            warmups=0,
            iterations=1,
        )
    except ValueError as exc:
        assert "case_repetitions" in str(exc)
    else:
        raise AssertionError("Expected invalid case repetitions to fail.")


def test_quality_benchmark_rejects_invalid_reproducibility_repetitions() -> None:
    try:
        run_benchmark(
            case_repetitions=1,
            reproducibility_repetitions=0,
            warmups=0,
            iterations=1,
        )
    except ValueError as exc:
        assert "reproducibility_repetitions" in str(exc)
    else:
        raise AssertionError(
            "Expected invalid reproducibility repetitions to fail."
        )


def test_detection_rate_is_perfect_for_known_regressions() -> None:
    payload = run_benchmark(
        case_repetitions=2,
        reproducibility_repetitions=2,
        warmups=0,
        iterations=1,
    )

    assert payload["detection"]["minimum_detection_rate"] == 1.0


def test_false_positive_rate_is_zero_for_known_clean_cases() -> None:
    payload = run_benchmark(
        case_repetitions=2,
        reproducibility_repetitions=2,
        warmups=0,
        iterations=1,
    )

    assert payload["false_positives"]["maximum_false_positive_rate"] == 0.0


def test_reproducibility_is_perfect() -> None:
    payload = run_benchmark(
        case_repetitions=2,
        reproducibility_repetitions=10,
        warmups=0,
        iterations=1,
    )

    assert payload["reproducibility"]["reproducibility_rate"] == 1.0
