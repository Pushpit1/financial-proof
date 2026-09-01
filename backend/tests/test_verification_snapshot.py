from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.models.verification_snapshot import VerificationSnapshot


def test_verification_snapshot_has_stable_identity() -> None:
    snapshot = VerificationSnapshot(
        contract_version="contract-v1",
        system_version="system-v1",
    )

    assert snapshot.snapshot_id is not None
    assert snapshot.created_at is not None


def test_verification_snapshot_preserves_verification_context() -> None:
    contract_id = uuid4()
    simulation_id = uuid4()
    counterexample_id = uuid4()

    snapshot = VerificationSnapshot(
        contract_id=contract_id,
        contract_version="contract-v3",
        system_version="system-2026.09",
        baseline={"balance": 1000},
        violations=("refund_without_approval",),
        counterexample_ids=(counterexample_id,),
        simulation_id=simulation_id,
        reproducibility_metadata={
            "seed": 42,
            "engine": "deterministic",
        },
    )

    assert snapshot.contract_id == contract_id
    assert snapshot.contract_version == "contract-v3"
    assert snapshot.system_version == "system-2026.09"
    assert snapshot.baseline == {"balance": 1000}
    assert snapshot.violations == ("refund_without_approval",)
    assert snapshot.counterexample_ids == (counterexample_id,)
    assert snapshot.simulation_id == simulation_id
    assert snapshot.reproducibility_metadata["seed"] == 42


def test_verification_snapshot_is_immutable() -> None:
    snapshot = VerificationSnapshot(
        contract_version="contract-v1",
        system_version="system-v1",
    )

    with pytest.raises(ValidationError):
        snapshot.system_version = "system-v2"
