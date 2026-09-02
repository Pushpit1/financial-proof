"""Tests for the canonical Financial Proof demo seed."""

from datetime import UTC
from decimal import Decimal

from app.demo.seed import (
    DEMO_AMOUNT_MINOR,
    DEMO_AUTHORIZED_ACTOR,
    DEMO_BUSINESS_RULE,
    DEMO_CONTRACT_ID,
    DEMO_CURRENCY,
    DEMO_ORDER_ID,
    DEMO_PAYMENT_ID,
    DEMO_SEED,
    DEMO_SIMULATION_ID,
    DEMO_UNAUTHORIZED_ACTOR,
    build_demo_seed,
)
from app.domain.enums.financial import ClaimType
from app.domain.services.payment_simulation_runner import (
    PaymentSimulationRunner,
)


def test_demo_seed_is_deterministic() -> None:
    first = build_demo_seed()
    second = build_demo_seed()

    assert first == second
    assert first.contract_id == DEMO_CONTRACT_ID
    assert first.order_id == DEMO_ORDER_ID
    assert first.payment_id == DEMO_PAYMENT_ID
    assert first.simulation_id == DEMO_SIMULATION_ID
    assert first.seed == DEMO_SEED


def test_demo_seed_contains_canonical_business_scenario() -> None:
    demo = build_demo_seed()

    assert demo.business_rule == DEMO_BUSINESS_RULE
    assert demo.contract_name == "customer-refund-safety"
    assert demo.contract_version == 1
    assert demo.required_claim_types == (ClaimType.TRANSACTION,)
    assert demo.amount_minor == DEMO_AMOUNT_MINOR
    assert demo.currency == DEMO_CURRENCY


def test_demo_seed_contains_valid_ordered_payment_events() -> None:
    demo = build_demo_seed()

    assert [event.sequence for event in demo.events] == [0, 1]
    assert [event.event.value for event in demo.events] == [
        "authorize",
        "capture",
    ]
    assert all(event.occurred_at.tzinfo == UTC for event in demo.events)


def test_demo_seed_builds_replayable_simulation() -> None:
    demo = build_demo_seed()
    simulation = demo.build_simulation()

    first = PaymentSimulationRunner.run(simulation)
    replayed = PaymentSimulationRunner.replay(simulation)

    assert first == replayed
    assert first.simulation_id == DEMO_SIMULATION_ID
    assert first.seed == DEMO_SEED
    assert first.final_payment.state.value == "captured"
    assert first.final_order.state.value == "captured"


def test_demo_seed_has_deterministic_violation_fixture() -> None:
    demo = build_demo_seed()

    assert demo.violation_context["original_payment_amount"] == Decimal(
        "50.00"
    )
    assert demo.violation_context["refund_amount"] == Decimal("75.00")
    assert demo.violation_context["currency"] == DEMO_CURRENCY


def test_demo_seed_has_distinct_guardian_actors() -> None:
    demo = build_demo_seed()

    assert demo.unauthorized_actor == DEMO_UNAUTHORIZED_ACTOR
    assert demo.authorized_actor == DEMO_AUTHORIZED_ACTOR
    assert demo.unauthorized_actor != demo.authorized_actor
