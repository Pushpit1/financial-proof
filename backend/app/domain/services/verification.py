from time import perf_counter

import structlog

from app.core.metrics import get_metrics_registry
from app.core.observability import bind_observability_context
from app.domain.models.verification_comparison import (
    VerificationComparison,
)
from app.domain.models.verification_result import VerificationResult

logger = structlog.get_logger(__name__)


class VerificationService:
    """Deterministically evaluates a before/after comparison."""

    @staticmethod
    def verify(
        comparison: VerificationComparison,
    ) -> VerificationResult:
        """Produce a deterministic verification result."""

        started_at = perf_counter()

        violations = tuple(
            sorted(comparison.introduced_violations),
        )

        regression_detected = bool(
            comparison.regression_detected
            or violations
        )

        result = VerificationResult(
            before_snapshot_id=comparison.before_snapshot_id,
            after_snapshot_id=comparison.after_snapshot_id,
            comparison_id=comparison.comparison_id,
            passed=not regression_detected,
            regression_detected=regression_detected,
            violations=violations,
        )

        bind_observability_context(
            verification_id=str(result.verification_id),
        )

        metrics = get_metrics_registry()
        metrics.counter("verification_runs_total").increment()
        metrics.histogram(
            "verification_latency_seconds",
        ).observe(
            perf_counter() - started_at,
        )

        if result.regression_detected:
            metrics.counter(
                "verification_regressions_total",
            ).increment()

        if result.violations:
            metrics.counter(
                "verification_violations_total",
            ).increment(len(result.violations))

        logger.info(
            "verification_completed",
            verification_id=str(result.verification_id),
            comparison_id=str(result.comparison_id),
            before_snapshot_id=str(result.before_snapshot_id),
            after_snapshot_id=str(result.after_snapshot_id),
            passed=result.passed,
            regression_detected=result.regression_detected,
            violation_count=len(result.violations),
        )

        return result
