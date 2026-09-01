import structlog

from app.core.observability import bind_observability_context
from app.domain.models.verification_comparison import (
    VerificationChange,
    VerificationComparison,
)
from app.domain.models.verification_snapshot import VerificationSnapshot

logger = structlog.get_logger(__name__)


class VerificationComparisonService:
    """Deterministically compares two verification snapshots."""

    @staticmethod
    def compare(
        before: VerificationSnapshot,
        after: VerificationSnapshot,
    ) -> VerificationComparison:
        """Compare before/after verification evidence."""

        changes: list[VerificationChange] = []

        baseline_keys = sorted(
            set(before.baseline) | set(after.baseline),
        )

        for field in baseline_keys:
            before_value = before.baseline.get(field)
            after_value = after.baseline.get(field)

            if before_value != after_value:
                changes.append(
                    VerificationChange(
                        field=field,
                        before=before_value,
                        after=after_value,
                        change_type="baseline_field_changed",
                    ),
                )

        before_violations = set(before.violations)
        after_violations = set(after.violations)

        introduced_violations = tuple(
            sorted(after_violations - before_violations),
        )
        resolved_violations = tuple(
            sorted(before_violations - after_violations),
        )

        for violation in introduced_violations:
            changes.append(
                VerificationChange(
                    field=f"violation:{violation}",
                    before=False,
                    after=True,
                    change_type="violation_introduced",
                ),
            )

        for violation in resolved_violations:
            changes.append(
                VerificationChange(
                    field=f"violation:{violation}",
                    before=True,
                    after=False,
                    change_type="violation_resolved",
                ),
            )

        changes.sort(key=lambda change: change.field)

        before_keys = set(before.baseline)
        after_keys = set(after.baseline)

        added_changes = tuple(
            sorted(after_keys - before_keys),
        )
        removed_changes = tuple(
            sorted(before_keys - after_keys),
        )

        before_counterexamples = set(before.counterexample_ids)
        after_counterexamples = set(after.counterexample_ids)

        added_counterexample_ids = tuple(
            sorted(after_counterexamples - before_counterexamples),
        )
        removed_counterexample_ids = tuple(
            sorted(before_counterexamples - after_counterexamples),
        )

        comparison = VerificationComparison(
            before_snapshot_id=before.snapshot_id,
            after_snapshot_id=after.snapshot_id,
            contract_version_changed=(
                before.contract_version != after.contract_version
            ),
            system_version_changed=(
                before.system_version != after.system_version
            ),
            changes=tuple(changes),
            added_changes=added_changes,
            removed_changes=removed_changes,
            introduced_violations=introduced_violations,
            resolved_violations=resolved_violations,
            added_counterexample_ids=added_counterexample_ids,
            removed_counterexample_ids=removed_counterexample_ids,
            regression_detected=bool(introduced_violations),
        )

        bind_observability_context(
            contract_id=(
                str(after.contract_id)
                if after.contract_id is not None
                else (
                    str(before.contract_id)
                    if before.contract_id is not None
                    else None
                )
            ),
            simulation_id=(
                str(after.simulation_id)
                if after.simulation_id is not None
                else (
                    str(before.simulation_id)
                    if before.simulation_id is not None
                    else None
                )
            ),
        )

        logger.info(
            "verification_comparison_completed",
            comparison_id=str(comparison.comparison_id),
            before_snapshot_id=str(comparison.before_snapshot_id),
            after_snapshot_id=str(comparison.after_snapshot_id),
            introduced_violation_count=len(
                comparison.introduced_violations,
            ),
            resolved_violation_count=len(
                comparison.resolved_violations,
            ),
            added_counterexample_ids=[
                str(counterexample_id)
                for counterexample_id in comparison.added_counterexample_ids
            ],
            removed_counterexample_ids=[
                str(counterexample_id)
                for counterexample_id in comparison.removed_counterexample_ids
            ],
            regression_detected=comparison.regression_detected,
        )

        return comparison
