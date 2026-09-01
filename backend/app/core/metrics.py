"""Deterministic application metrics primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class Counter:
    """Monotonically increasing metric counter."""

    name: str
    _value: int = 0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def increment(self, amount: int = 1) -> None:
        """Increase the counter by a positive amount."""
        if amount < 0:
            raise ValueError("Counter increment must be non-negative.")

        with self._lock:
            self._value += amount

    @property
    def value(self) -> int:
        """Return the current counter value."""
        with self._lock:
            return self._value


@dataclass
class Histogram:
    """Metric for recording non-negative numeric observations."""

    name: str
    _values: list[float] = field(default_factory=list)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def observe(self, value: float) -> None:
        """Record one non-negative observation."""
        if value < 0:
            raise ValueError("Histogram observations must be non-negative.")

        with self._lock:
            self._values.append(float(value))

    @property
    def count(self) -> int:
        """Return the number of observations."""
        with self._lock:
            return len(self._values)

    @property
    def total(self) -> float:
        """Return the sum of all observations."""
        with self._lock:
            return sum(self._values)

    @property
    def minimum(self) -> float | None:
        """Return the smallest observation."""
        with self._lock:
            return min(self._values) if self._values else None

    @property
    def maximum(self) -> float | None:
        """Return the largest observation."""
        with self._lock:
            return max(self._values) if self._values else None

    @property
    def average(self) -> float | None:
        """Return the average observation."""
        with self._lock:
            if not self._values:
                return None

            return sum(self._values) / len(self._values)

    def snapshot(self) -> dict[str, float | int | None]:
        """Return a deterministic summary of observations."""
        return {
            "count": self.count,
            "total": self.total,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "average": self.average,
        }


class MetricsRegistry:
    """Central registry for application counters and histograms."""

    def __init__(self) -> None:
        self._counters: dict[str, Counter] = {}
        self._histograms: dict[str, Histogram] = {}
        self._lock = Lock()

    def counter(self, name: str) -> Counter:
        """Return or create a named counter."""
        self._validate_name(name)

        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name=name)

            return self._counters[name]

    def histogram(self, name: str) -> Histogram:
        """Return or create a named histogram."""
        self._validate_name(name)

        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name=name)

            return self._histograms[name]

    def snapshot(self) -> dict[str, dict[str, object]]:
        """Return all registered metric values."""
        with self._lock:
            counters = {
                name: {"value": counter.value}
                for name, counter in sorted(self._counters.items())
            }

            histograms = {
                name: histogram.snapshot()
                for name, histogram in sorted(self._histograms.items())
            }

        return {
            "counters": counters,
            "histograms": histograms,
        }

    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate a metric name."""
        if not name.strip():
            raise ValueError("Metric name must not be empty.")


_default_registry = MetricsRegistry()


def get_metrics_registry() -> MetricsRegistry:
    """Return the process-wide application metrics registry."""
    return _default_registry
