"""Tests for verification throughput benchmarks."""

from __future__ import annotations

import json

import pytest

from benchmarks.verification_throughput import (
    run_benchmark,
)


def test_verification_benchmark_runs(tmp_path, monkeypatch) -> None:
    import benchmarks.verification_throughput as module

    monkeypatch.setattr(module, "RESULTS_PATH", tmp_path)

    payload = run_benchmark(
        verification_count=3,
        warmups=0,
        iterations=2,
    )

    assert payload["workload"] == {
        "verification_count": 3,
    }

    assert payload["clean"]["iterations"] == 2
    assert payload["regression"]["iterations"] == 2

    assert payload["clean"]["throughput_per_second"] > 0
    assert payload["regression"]["throughput_per_second"] > 0


def test_verification_benchmark_writes_result(tmp_path, monkeypatch) -> None:
    import benchmarks.verification_throughput as module

    monkeypatch.setattr(module, "RESULTS_PATH", tmp_path)

    run_benchmark(
        verification_count=2,
        warmups=0,
        iterations=1,
    )

    result_path = tmp_path / "verification_2.json"

    assert result_path.exists()

    payload = json.loads(
        result_path.read_text(encoding="utf-8"),
    )

    assert payload["workload"]["verification_count"] == 2


def test_verification_benchmark_rejects_invalid_count() -> None:
    with pytest.raises(ValueError):
        run_benchmark(
            verification_count=0,
        )
