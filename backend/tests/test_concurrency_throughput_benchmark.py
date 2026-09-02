from benchmarks.concurrency_throughput import (
    run_benchmark,
)


def test_concurrency_benchmark_rejects_invalid_worker_count() -> None:
    try:
        run_benchmark(
            worker_count=0,
            warmups=0,
            iterations=1,
        )
    except ValueError as exc:
        assert "at least 1" in str(exc)
    else:
        raise AssertionError("Expected invalid worker count to fail.")


def test_concurrency_benchmark_preserves_same_key_exactly_once() -> None:
    payload = run_benchmark(
        worker_count=4,
        warmups=0,
        iterations=1,
    )

    assert payload["correctness"]["same_key_executions"] == [1]


def test_concurrency_benchmark_executes_independent_keys() -> None:
    payload = run_benchmark(
        worker_count=4,
        warmups=0,
        iterations=1,
    )

    assert payload["correctness"]["independent_key_executions"] == [4]


def test_concurrency_benchmark_persists_result() -> None:
    payload = run_benchmark(
        worker_count=2,
        warmups=0,
        iterations=1,
    )

    assert payload["benchmark"]["name"] == "idempotent_concurrency"
