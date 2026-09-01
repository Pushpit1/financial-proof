import pytest

from app.core.metrics import Counter, Histogram, MetricsRegistry


def test_counter_starts_at_zero() -> None:
    counter = Counter(name="test_counter")

    assert counter.value == 0


def test_counter_increments() -> None:
    counter = Counter(name="test_counter")

    counter.increment()
    counter.increment(4)

    assert counter.value == 5


def test_counter_rejects_negative_increment() -> None:
    counter = Counter(name="test_counter")

    with pytest.raises(ValueError, match="non-negative"):
        counter.increment(-1)


def test_histogram_records_observations() -> None:
    histogram = Histogram(name="test_latency")

    histogram.observe(0.1)
    histogram.observe(0.3)
    histogram.observe(0.5)

    assert histogram.count == 3
    assert histogram.total == pytest.approx(0.9)
    assert histogram.minimum == pytest.approx(0.1)
    assert histogram.maximum == pytest.approx(0.5)
    assert histogram.average == pytest.approx(0.3)


def test_histogram_empty_snapshot() -> None:
    histogram = Histogram(name="test_latency")

    assert histogram.snapshot() == {
        "count": 0,
        "total": 0,
        "minimum": None,
        "maximum": None,
        "average": None,
    }


def test_histogram_rejects_negative_observation() -> None:
    histogram = Histogram(name="test_latency")

    with pytest.raises(ValueError, match="non-negative"):
        histogram.observe(-0.1)


def test_registry_reuses_named_counter() -> None:
    registry = MetricsRegistry()

    first = registry.counter("operations")
    second = registry.counter("operations")

    assert first is second

    first.increment(3)

    assert second.value == 3


def test_registry_reuses_named_histogram() -> None:
    registry = MetricsRegistry()

    first = registry.histogram("latency")
    second = registry.histogram("latency")

    assert first is second

    first.observe(1.25)

    assert second.count == 1


def test_registry_snapshot_is_deterministic() -> None:
    registry = MetricsRegistry()

    registry.counter("z_counter").increment(2)
    registry.counter("a_counter").increment(1)
    registry.histogram("z_latency").observe(2.0)
    registry.histogram("a_latency").observe(1.0)

    assert registry.snapshot() == {
        "counters": {
            "a_counter": {"value": 1},
            "z_counter": {"value": 2},
        },
        "histograms": {
            "a_latency": {
                "count": 1,
                "total": 1.0,
                "minimum": 1.0,
                "maximum": 1.0,
                "average": 1.0,
            },
            "z_latency": {
                "count": 1,
                "total": 2.0,
                "minimum": 2.0,
                "maximum": 2.0,
                "average": 2.0,
            },
        },
    }


def test_registry_rejects_empty_metric_name() -> None:
    registry = MetricsRegistry()

    with pytest.raises(ValueError, match="must not be empty"):
        registry.counter(" ")

    with pytest.raises(ValueError, match="must not be empty"):
        registry.histogram("")
