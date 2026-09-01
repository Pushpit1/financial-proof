from uuid import uuid4

from app.core.config import settings
from app.domain.models.financial import FinancialContract
from app.domain.services.verification_snapshot import (
    VerificationSnapshotService,
)


def test_capture_for_contract_uses_canonical_versions() -> None:
    contract = FinancialContract(
        id=uuid4(),
        name="test-contract",
        version=7,
    )

    snapshot = VerificationSnapshotService.capture_for_contract(
        contract=contract,
    )

    assert snapshot.contract_id == contract.id
    assert snapshot.contract_version == "7"
    assert snapshot.system_version == settings.app_version


def test_capture_baseline_allows_explicit_versions() -> None:
    snapshot = VerificationSnapshotService.capture_baseline(
        contract_version="42",
        system_version="9.9.9",
    )

    assert snapshot.contract_version == "42"
    assert snapshot.system_version == "9.9.9"


def test_capture_for_contract_preserves_verification_evidence() -> None:
    contract = FinancialContract(
        name="evidence-contract",
        version=3,
    )
    simulation_id = uuid4()
    counterexample_id = uuid4()

    snapshot = VerificationSnapshotService.capture_for_contract(
        contract=contract,
        baseline={"balance": "1000"},
        violations=("negative_balance",),
        counterexample_ids=(counterexample_id,),
        simulation_id=simulation_id,
        reproducibility_metadata={"seed": 123},
    )

    assert snapshot.baseline == {"balance": "1000"}
    assert snapshot.violations == ("negative_balance",)
    assert snapshot.counterexample_ids == (counterexample_id,)
    assert snapshot.simulation_id == simulation_id
    assert snapshot.reproducibility_metadata == {"seed": 123}
