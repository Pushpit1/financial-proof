import pytest

import benchmarks.concurrency_throughput as benchmark_module


@pytest.fixture(autouse=True)
def isolate_benchmark_output(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(benchmark_module, "RESULTS_PATH", tmp_path)


def test_concurrency_benchmark_rejects_invalid_worker_count() -> None:
    try:
        benchmark_module.run_benchmark(
            worker_count=0,
            warmups=0,
            iterations=1,
        )
    except ValueError as exc:
        assert "at least 1" in str(exc)
    else:
        raise AssertionError("Expected invalid worker count to fail.")


def test_concurrency_benchmark_preserves_same_key_exactly_once() -> None:
    payload = benchmark_module.run_benchmark(
        worker_count=4,
        warmups=0,
        iterations=1,
    )

    assert payload["correctness"]["same_key_executions"] == [1]


def test_concurrency_benchmark_executes_independent_keys() -> None:
    payload = benchmark_module.run_benchmark(
        worker_count=4,
        warmups=0,
        iterations=1,
    )

    assert payload["correctness"]["independent_key_executions"] == [4]


def test_concurrency_benchmark_persists_result(tmp_path) -> None:
    payload = benchmark_module.run_benchmark(
        worker_count=2,
        warmups=0,
        iterations=1,
    )

    assert payload["benchmark"]["name"] == "idempotent_concurrency"
    assert (tmp_path / "concurrency_2.json").is_file()
