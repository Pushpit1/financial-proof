from uuid import uuid4

from app.domain.services.verification_snapshot import (
    VerificationSnapshotService,
)


def test_capture_baseline_creates_snapshot() -> None:
    contract_id = uuid4()
    simulation_id = uuid4()
    counterexample_id = uuid4()

    snapshot = VerificationSnapshotService.capture_baseline(
        contract_id=contract_id,
        contract_version="contract-v2",
        system_version="system-v5",
        baseline={"balance": 1000, "status": "active"},
        violations=("refund_without_approval",),
        counterexample_ids=(counterexample_id,),
        simulation_id=simulation_id,
        reproducibility_metadata={"seed": 42},
    )

    assert snapshot.contract_id == contract_id
    assert snapshot.contract_version == "contract-v2"
    assert snapshot.system_version == "system-v5"
    assert snapshot.baseline == {
        "balance": 1000,
        "status": "active",
    }
    assert snapshot.violations == ("refund_without_approval",)
    assert snapshot.counterexample_ids == (counterexample_id,)
    assert snapshot.simulation_id == simulation_id
    assert snapshot.reproducibility_metadata == {"seed": 42}


def test_capture_baseline_defensively_copies_input() -> None:
    baseline = {"balance": 1000}
    metadata = {"seed": 42}

    snapshot = VerificationSnapshotService.capture_baseline(
        contract_version="contract-v1",
        system_version="system-v1",
        baseline=baseline,
        reproducibility_metadata=metadata,
    )

    baseline["balance"] = 0
    metadata["seed"] = 999

    assert snapshot.baseline == {"balance": 1000}
    assert snapshot.reproducibility_metadata == {"seed": 42}


def test_capture_baseline_defaults_empty_collections() -> None:
    snapshot = VerificationSnapshotService.capture_baseline(
        contract_version="contract-v1",
        system_version="system-v1",
    )

    assert snapshot.baseline == {}
    assert snapshot.violations == ()
    assert snapshot.counterexample_ids == ()
    assert snapshot.reproducibility_metadata == {}
