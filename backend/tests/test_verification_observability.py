import json
from uuid import uuid4

from app.core.logging import configure_logging
from app.core.observability import (
    bind_observability_context,
    clear_observability_context,
    get_observability_context,
)
from app.domain.models.verification_snapshot import VerificationSnapshot
from app.domain.services.verification import VerificationService
from app.domain.services.verification_comparison import (
    VerificationComparisonService,
)
from app.domain.services.verification_snapshot import (
    VerificationSnapshotService,
)


def _log_events(captured: str) -> list[dict[str, object]]:
    events = []

    for line in captured.splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue

        if "event" in payload:
            events.append(payload)

    return events


def test_verification_snapshot_emits_observability_event(capsys) -> None:
    configure_logging()

    contract_id = uuid4()
    simulation_id = uuid4()
    counterexample_id = uuid4()

    snapshot = VerificationSnapshotService.capture_baseline(
        contract_id=contract_id,
        simulation_id=simulation_id,
        counterexample_ids=(counterexample_id,),
    )

    events = _log_events(capsys.readouterr().out)

    event = next(
        item
        for item in events
        if item["event"] == "verification_snapshot_captured"
    )

    assert event["snapshot_id"] == str(snapshot.snapshot_id)
    assert event["contract_id"] == str(contract_id)
    assert event["simulation_id"] == str(simulation_id)
    assert event["counterexample_ids"] == [str(counterexample_id)]


def test_verification_comparison_emits_observability_event(capsys) -> None:
    configure_logging()

    contract_id = uuid4()
    simulation_id = uuid4()

    before = VerificationSnapshot(
        contract_id=contract_id,
        contract_version="1",
        system_version="1.0",
        simulation_id=simulation_id,
    )
    after = VerificationSnapshot(
        contract_id=contract_id,
        contract_version="1",
        system_version="1.0",
        simulation_id=simulation_id,
        violations=("payment_limit_exceeded",),
    )

    comparison = VerificationComparisonService.compare(
        before,
        after,
    )

    events = _log_events(capsys.readouterr().out)

    event = next(
        item
        for item in events
        if item["event"] == "verification_comparison_completed"
    )

    assert event["comparison_id"] == str(comparison.comparison_id)
    assert event["before_snapshot_id"] == str(before.snapshot_id)
    assert event["after_snapshot_id"] == str(after.snapshot_id)
    assert event["regression_detected"] is True
    assert event["introduced_violation_count"] == 1


def test_verification_emits_verification_id(capsys) -> None:
    configure_logging()

    before = VerificationSnapshot(
        contract_version="1",
        system_version="1.0",
    )
    after = VerificationSnapshot(
        contract_version="1",
        system_version="1.0",
        violations=("payment_limit_exceeded",),
    )

    comparison = VerificationComparisonService.compare(
        before,
        after,
    )
    result = VerificationService.verify(comparison)

    events = _log_events(capsys.readouterr().out)

    event = next(
        item
        for item in events
        if item["event"] == "verification_completed"
    )

    assert event["verification_id"] == str(result.verification_id)
    assert event["comparison_id"] == str(result.comparison_id)
    assert event["passed"] is False
    assert event["regression_detected"] is True


def test_observability_context_contains_verification_identifiers() -> None:
    clear_observability_context()

    bind_observability_context(
        contract_id="contract-1",
        simulation_id="simulation-1",
    )

    before = VerificationSnapshot(
        contract_version="1",
        system_version="1.0",
    )
    after = VerificationSnapshot(
        contract_version="1",
        system_version="1.0",
        violations=("payment_limit_exceeded",),
    )

    comparison = VerificationComparisonService.compare(
        before,
        after,
    )
    result = VerificationService.verify(comparison)

    context = get_observability_context()

    assert context["contract_id"] == "contract-1"
    assert context["simulation_id"] == "simulation-1"
    assert context["verification_id"] == str(result.verification_id)

    clear_observability_context()
