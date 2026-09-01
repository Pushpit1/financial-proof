from app.core.metrics import MetricsRegistry


def test_runtime_metric_names_are_supported() -> None:
    registry = MetricsRegistry()

    counter_names = (
        "simulation_runs_total",
        "verification_runs_total",
        "verification_regressions_total",
        "verification_violations_total",
        "counterexample_shrinks_total",
        "counterexample_shrink_rejections_total",
        "counterexample_chunk_shrinks_total",
        "counterexample_chunk_shrink_rejections_total",
        "guardian_decisions_total",
        "ai_investigations_total",
        "ai_investigation_success_total",
        "ai_investigation_forbidden_total",
        "ai_investigation_not_found_total",
        "ai_investigation_denied_total",
        "ai_investigation_invalid_input_total",
        "ai_investigation_failed_total",
    )

    for name in counter_names:
        registry.counter(name).increment()

    registry.histogram(
        "verification_latency_seconds",
    ).observe(0.25)

    snapshot = registry.snapshot()

    for name in counter_names:
        assert snapshot["counters"][name]["value"] == 1

    assert snapshot["histograms"]["verification_latency_seconds"] == {
        "count": 1,
        "total": 0.25,
        "minimum": 0.25,
        "maximum": 0.25,
        "average": 0.25,
    }
