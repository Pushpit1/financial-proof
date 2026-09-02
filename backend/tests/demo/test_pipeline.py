from decimal import Decimal

from app.demo.pipeline import DemoPipeline
from app.demo.seed import build_demo_seed


def test_demo_pipeline_compiles_canonical_contract() -> None:
    seed = build_demo_seed()
    pipeline = DemoPipeline(seed)

    contract = pipeline.compile_contract()

    assert contract.id == seed.contract_id
    assert contract.name == seed.contract_name
    assert contract.version == seed.contract_version
    assert contract.required_claim_types == seed.required_claim_types
    assert len(contract.financial_constraints) == 1

    constraint = contract.financial_constraints[0]

    assert constraint.field == "refund_amount"
    assert constraint.currency == "INR"
    assert constraint.value == Decimal("50.00")


def test_demo_pipeline_baseline_is_deterministic() -> None:
    seed = build_demo_seed()
    pipeline = DemoPipeline(seed)

    first = pipeline.run_baseline()
    second = pipeline.run_baseline()

    assert first == second
    assert first.simulation_id == seed.simulation_id
    assert first.seed == seed.seed
    assert len(first.trace) == 2
    assert len(first.snapshots) == 2


def test_demo_pipeline_attack_is_deterministic() -> None:
    seed = build_demo_seed()

    first = DemoPipeline(seed).run_attack()
    second = DemoPipeline(seed).run_attack()

    assert first.simulation_id == second.simulation_id
    assert first.adversarial_simulation == second.adversarial_simulation
    assert first.scenario == second.scenario
    assert first.outcomes == second.outcomes

    assert first.attack_count == 1
    assert first.applied_components == ("DuplicateEventAttack",)
    assert len(first.adversarial_simulation.events) == 3

    events = tuple(
        event.event
        for event in first.adversarial_simulation.events
    )

    baseline_events = seed.build_simulation().events

    assert events == (
        baseline_events[0].event,
        baseline_events[0].event,
        baseline_events[1].event,
    )


def test_demo_pipeline_evaluates_financial_violation() -> None:
    seed = build_demo_seed()
    pipeline = DemoPipeline(seed)
    contract = pipeline.compile_contract()

    evaluation = pipeline.evaluate_attack(contract)

    assert not evaluation.passed
    assert evaluation.violation_count == 1

    violation = evaluation.violations[0]

    assert violation.reason_code == "financial_constraint_failed"
    assert violation.field == "refund_amount"


def test_demo_pipeline_builds_verification_and_counterexample() -> None:
    seed = build_demo_seed()
    pipeline = DemoPipeline(seed)
    contract = pipeline.compile_contract()

    comparison, verification, counterexample = pipeline.build_verification(
        contract
    )

    assert comparison.regression_detected is True
    assert comparison.introduced_violations == (
        "financial_constraint_failed",
    )

    assert verification.passed is False
    assert verification.regression_detected is True
    assert verification.violations == (
        "financial_constraint_failed",
    )

    assert counterexample.simulation_id == seed.simulation_id
    assert counterexample.simulation.id == seed.simulation_id
    assert counterexample.violation_code == "financial_constraint_failed"
    assert counterexample.original_event_count == 3
    assert counterexample.minimized_event_count == 3
    assert len(counterexample.simulation.events) == 3


def test_demo_pipeline_verification_is_reproducible() -> None:
    seed = build_demo_seed()
    contract = DemoPipeline(seed).compile_contract()

    first = DemoPipeline(seed).build_verification(contract)
    second = DemoPipeline(seed).build_verification(contract)

    assert first[0].introduced_violations == second[0].introduced_violations
    assert first[0].regression_detected == second[0].regression_detected
    assert first[1].passed == second[1].passed
    assert first[1].violations == second[1].violations
    assert first[2].simulation == second[2].simulation


def test_demo_pipeline_shrinks_counterexample() -> None:
    seed = build_demo_seed()
    pipeline = DemoPipeline(seed)
    contract = pipeline.compile_contract()

    counterexample = pipeline.shrink_counterexample(contract)

    assert counterexample.simulation_id == seed.simulation_id
    assert counterexample.original_event_count == 3
    assert counterexample.minimized_event_count == 2
    assert len(counterexample.simulation.events) == 2

    assert tuple(
        event.event
        for event in counterexample.simulation.events
    ) == (
        seed.build_simulation().events[0].event,
        seed.build_simulation().events[0].event,
    )


def test_demo_pipeline_shrinking_is_deterministic() -> None:
    seed = build_demo_seed()
    contract = DemoPipeline(seed).compile_contract()

    first = DemoPipeline(seed).shrink_counterexample(contract)
    second = DemoPipeline(seed).shrink_counterexample(contract)

    assert first.simulation == second.simulation
    assert first.violation_code == second.violation_code
    assert first.original_event_count == second.original_event_count
    assert first.minimized_event_count == second.minimized_event_count


def test_demo_pipeline_rejects_shrinking_when_verification_passes() -> None:
    seed = build_demo_seed()
    pipeline = DemoPipeline(seed)

    class PassingPipeline(DemoPipeline):
        def build_verification(self, contract):
            comparison, verification, counterexample = super().build_verification(
                contract
            )
            return (
                comparison.model_copy(
                    update={
                        "regression_detected": False,
                        "introduced_violations": (),
                    }
                ),
                verification.model_copy(
                    update={
                        "passed": True,
                        "regression_detected": False,
                        "violations": (),
                    }
                ),
                counterexample,
            )

    passing_pipeline = PassingPipeline(seed)

    try:
        passing_pipeline.shrink_counterexample(
            pipeline.compile_contract()
        )
    except ValueError as exc:
        assert str(exc) == "Cannot shrink a passing demo verification."
    else:
        raise AssertionError("Expected passing verification to be rejected.")


def test_demo_pipeline_preserves_seed_identity() -> None:
    seed = build_demo_seed()
    pipeline = DemoPipeline(seed)

    assert pipeline.seed == seed
    assert pipeline.seed.contract_id == seed.contract_id
    assert pipeline.seed.simulation_id == seed.simulation_id
