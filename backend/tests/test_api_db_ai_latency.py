"""Tests for M21 API, DB, and AI latency benchmarks."""

from __future__ import annotations

import json

import benchmarks.api_db_ai_latency as benchmark_module


def test_api_benchmark_returns_representative_endpoints() -> None:
    result = benchmark_module.run_api_benchmark()

    assert set(result["measurements"]) == {
        "health_get",
        "ready_get",
        "contract_get_by_id",
        "contract_create",
    }

    for measurement in result["measurements"].values():
        assert measurement["iterations"] == benchmark_module.ITERATIONS
        assert measurement["average_seconds"] >= 0
        assert measurement["throughput_per_second"] > 0


def test_db_benchmark_returns_real_sqlite_measurements() -> None:
    result = benchmark_module.run_db_benchmark()

    assert result["database"] == "sqlite_in_memory"
    assert set(result["measurements"]) == {
        "select_1",
        "contract_insert_and_flush",
    }

    for measurement in result["measurements"].values():
        assert measurement["average_seconds"] >= 0
        assert measurement["throughput_per_second"] > 0


def test_ai_benchmark_uses_real_investigation_engine() -> None:
    result = benchmark_module.run_ai_benchmark()

    assert result["tool"] == "inspect_contract"
    assert result["measurement"]["iterations"] == (
        benchmark_module.ITERATIONS
    )
    assert result["measurement"]["average_seconds"] >= 0
    assert result["measurement"]["throughput_per_second"] > 0
    assert result["cost"]["measurable"] is False


def test_full_task10_benchmark_writes_results(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(benchmark_module, "RESULTS_DIR", tmp_path)

    result = benchmark_module.run_benchmark()

    output = tmp_path / "api_db_ai_latency.json"

    assert output.exists()
    persisted = json.loads(output.read_text(encoding="utf-8"))

    assert persisted["benchmark"] == result["benchmark"]
    assert "api" in persisted
    assert "db" in persisted
    assert "ai" in persisted
