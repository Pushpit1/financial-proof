from typing import Any
from uuid import UUID

import structlog

from app.core.config import settings
from app.core.observability import bind_observability_context
from app.domain.models.financial import FinancialContract
from app.domain.models.verification_snapshot import VerificationSnapshot

logger = structlog.get_logger(__name__)


class VerificationSnapshotService:
    """Creates immutable verification snapshots from explicit evidence."""

    @staticmethod
    def capture_baseline(
        *,
        contract_version: str | None = None,
        system_version: str | None = None,
        baseline: dict[str, Any] | None = None,
        contract_id: UUID | None = None,
        violations: tuple[str, ...] = (),
        counterexample_ids: tuple[UUID, ...] = (),
        simulation_id: UUID | None = None,
        reproducibility_metadata: dict[str, Any] | None = None,
    ) -> VerificationSnapshot:
        """Capture a deterministic immutable verification baseline."""

        snapshot = VerificationSnapshot(
            contract_id=contract_id,
            contract_version=(
                contract_version
                if contract_version is not None
                else "unknown"
            ),
            system_version=(
                system_version
                if system_version is not None
                else settings.app_version
            ),
            baseline=dict(baseline or {}),
            violations=tuple(violations),
            counterexample_ids=tuple(counterexample_ids),
            simulation_id=simulation_id,
            reproducibility_metadata=dict(
                reproducibility_metadata or {},
            ),
        )

        bind_observability_context(
            contract_id=(
                str(snapshot.contract_id)
                if snapshot.contract_id is not None
                else None
            ),
            simulation_id=(
                str(snapshot.simulation_id)
                if snapshot.simulation_id is not None
                else None
            ),
        )

        logger.info(
            "verification_snapshot_captured",
            snapshot_id=str(snapshot.snapshot_id),
            contract_id=(
                str(snapshot.contract_id)
                if snapshot.contract_id is not None
                else None
            ),
            simulation_id=(
                str(snapshot.simulation_id)
                if snapshot.simulation_id is not None
                else None
            ),
            counterexample_ids=[
                str(counterexample_id)
                for counterexample_id in snapshot.counterexample_ids
            ],
            violation_count=len(snapshot.violations),
        )

        return snapshot

    @staticmethod
    def capture_for_contract(
        *,
        contract: FinancialContract,
        baseline: dict[str, Any] | None = None,
        violations: tuple[str, ...] = (),
        counterexample_ids: tuple[UUID, ...] = (),
        simulation_id: UUID | None = None,
        reproducibility_metadata: dict[str, Any] | None = None,
    ) -> VerificationSnapshot:
        """Capture a snapshot using the canonical contract version."""

        snapshot = VerificationSnapshot(
            contract_id=contract.id,
            contract_version=str(contract.version),
            system_version=settings.app_version,
            baseline=dict(baseline or {}),
            violations=tuple(violations),
            counterexample_ids=tuple(counterexample_ids),
            simulation_id=simulation_id,
            reproducibility_metadata=dict(
                reproducibility_metadata or {},
            ),
        )

        bind_observability_context(
            contract_id=str(snapshot.contract_id),
            simulation_id=(
                str(snapshot.simulation_id)
                if snapshot.simulation_id is not None
                else None
            ),
        )

        logger.info(
            "verification_snapshot_captured",
            snapshot_id=str(snapshot.snapshot_id),
            contract_id=str(snapshot.contract_id),
            simulation_id=(
                str(snapshot.simulation_id)
                if snapshot.simulation_id is not None
                else None
            ),
            counterexample_ids=[
                str(counterexample_id)
                for counterexample_id in snapshot.counterexample_ids
            ],
            violation_count=len(snapshot.violations),
        )

        return snapshot
