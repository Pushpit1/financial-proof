"""Benchmark harness regression tests."""

from benchmarks.harness import benchmark


def test_benchmark_measures_requested_iterations() -> None:
    calls = 0

    def operation() -> int:
        nonlocal calls
        calls += 1
        return calls

    result, outputs = benchmark(
        "test-operation",
        workload_size=5,
        operation=operation,
        warmups=2,
        iterations=4,
    )

    assert calls == 6
    assert outputs == [3, 4, 5, 6]

    assert result.name == "test-operation"
    assert result.workload_size == 5
    assert result.warmups == 2
    assert result.iterations == 4
    assert result.total_seconds >= 0
    assert result.average_seconds >= 0
    assert result.minimum_seconds >= 0
    assert result.maximum_seconds >= result.minimum_seconds
    assert result.throughput_per_second > 0


def test_benchmark_serialization_contains_measured_fields() -> None:
    result, _ = benchmark(
        "serialization-test",
        workload_size=10,
        operation=lambda: None,
        warmups=0,
        iterations=2,
    )

    payload = result.as_dict()

    assert payload["name"] == "serialization-test"
    assert payload["workload_size"] == 10
    assert payload["warmups"] == 0
    assert payload["iterations"] == 2
    assert "total_seconds" in payload
    assert "average_seconds" in payload
    assert "minimum_seconds" in payload
    assert "maximum_seconds" in payload
    assert "throughput_per_second" in payload


def test_benchmark_rejects_invalid_configuration() -> None:
    def operation() -> None:
        return None

    invalid_cases = (
        ("", 1, 0, 1),
        ("invalid-workload", 0, 0, 1),
        ("invalid-warmups", 1, -1, 1),
        ("invalid-iterations", 1, 0, 0),
    )

    for name, workload_size, warmups, iterations in invalid_cases:
        try:
            benchmark(
                name,
                workload_size,
                operation,
                warmups=warmups,
                iterations=iterations,
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Expected ValueError for invalid configuration.")
