"""Deterministic before/after verification API routes."""

from fastapi import APIRouter, HTTPException, status

from app.domain.models.verification_comparison import (
    VerificationComparison,
)
from app.domain.models.verification_snapshot import VerificationSnapshot
from app.domain.services.verification import VerificationService
from app.domain.services.verification_comparison import (
    VerificationComparisonService,
)
from app.schemas.verification import (
    VerificationChangeResponse,
    VerificationComparisonResponse,
    VerificationRequest,
    VerificationResponse,
    VerificationResultResponse,
    VerificationSnapshotResponse,
)

router = APIRouter(
    prefix="/verification",
    tags=["verification"],
)


def _snapshot_from_request(
    snapshot_request,
) -> VerificationSnapshot:
    """Create an immutable domain snapshot from API input."""
    return VerificationSnapshot(
        contract_id=snapshot_request.contract_id,
        contract_version=snapshot_request.contract_version,
        system_version=snapshot_request.system_version,
        baseline=dict(snapshot_request.baseline),
        violations=tuple(snapshot_request.violations),
        counterexample_ids=tuple(snapshot_request.counterexample_ids),
        simulation_id=snapshot_request.simulation_id,
        reproducibility_metadata=dict(
            snapshot_request.reproducibility_metadata,
        ),
    )


def _snapshot_response(
    snapshot: VerificationSnapshot,
) -> VerificationSnapshotResponse:
    """Convert a domain snapshot into an API response."""
    return VerificationSnapshotResponse(
        snapshot_id=snapshot.snapshot_id,
        created_at=snapshot.created_at.isoformat(),
        contract_id=snapshot.contract_id,
        contract_version=snapshot.contract_version,
        system_version=snapshot.system_version,
        baseline=dict(snapshot.baseline),
        violations=list(snapshot.violations),
        counterexample_ids=list(snapshot.counterexample_ids),
        simulation_id=snapshot.simulation_id,
        reproducibility_metadata=dict(
            snapshot.reproducibility_metadata,
        ),
    )


def _comparison_response(
    comparison: VerificationComparison,
) -> VerificationComparisonResponse:
    """Convert a domain comparison into an API response."""
    return VerificationComparisonResponse(
        comparison_id=comparison.comparison_id,
        before_snapshot_id=comparison.before_snapshot_id,
        after_snapshot_id=comparison.after_snapshot_id,
        contract_version_changed=comparison.contract_version_changed,
        system_version_changed=comparison.system_version_changed,
        changes=[
            VerificationChangeResponse(
                field=change.field,
                before=change.before,
                after=change.after,
                change_type=change.change_type,
            )
            for change in comparison.changes
        ],
        added_changes=list(comparison.added_changes),
        removed_changes=list(comparison.removed_changes),
        introduced_violations=list(
            comparison.introduced_violations,
        ),
        resolved_violations=list(
            comparison.resolved_violations,
        ),
        added_counterexample_ids=list(
            comparison.added_counterexample_ids,
        ),
        removed_counterexample_ids=list(
            comparison.removed_counterexample_ids,
        ),
        regression_detected=comparison.regression_detected,
    )


@router.post(
    "",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
)
async def verify(
    request: VerificationRequest,
) -> VerificationResponse:
    """Execute deterministic before/after verification."""
    try:
        before = _snapshot_from_request(request.before)
        after = _snapshot_from_request(request.after)

        comparison = VerificationComparisonService.compare(
            before,
            after,
        )

        result = VerificationService.verify(comparison)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return VerificationResponse(
        result=VerificationResultResponse(
            verification_id=result.verification_id,
            before_snapshot_id=result.before_snapshot_id,
            after_snapshot_id=result.after_snapshot_id,
            comparison_id=result.comparison_id,
            passed=result.passed,
            regression_detected=result.regression_detected,
            violations=list(result.violations),
            reproducible=result.reproducible,
        ),
        before=_snapshot_response(before),
        after=_snapshot_response(after),
        comparison=_comparison_response(comparison),
    )

