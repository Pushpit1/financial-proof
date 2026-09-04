from datetime import UTC, datetime

import pytest

from app.api.routes.financial_simulation import _build_attack, _build_simulation
from app.domain.models.adversarial_simulation import OutOfOrderEventAttack
from app.schemas.financial_simulation import AttackRequest, SimulationCreateRequest


def make_simulation():
    return _build_simulation(
        SimulationCreateRequest(
            seed=207,
            amount_minor=25_000,
            currency="USD",
            events=[
                {
                    "event": "authorize",
                    "occurred_at": datetime(
                        2026, 9, 4, 12, 0, tzinfo=UTC
                    ),
                },
                {
                    "event": "capture",
                    "occurred_at": datetime(
                        2026, 9, 4, 12, 0, 1, tzinfo=UTC
                    ),
                },
                {
                    "event": "refund",
                    "occurred_at": datetime(
                        2026, 9, 4, 12, 0, 2, tzinfo=UTC
                    ),
                },
            ],
        )
    )


def test_out_of_order_request_accepts_source_sequence() -> None:
    request = AttackRequest(
        attack_type="out_of_order",
        source_sequence=2,
        target_sequence=1,
    )

    assert request.source_sequence == 2
    assert request.target_sequence == 1


def test_out_of_order_builds_typed_attack_with_both_sequences() -> None:
    simulation = make_simulation()

    attack = _build_attack(
        simulation,
        AttackRequest(
            attack_type="out_of_order",
            source_sequence=2,
            target_sequence=1,
        ),
    )

    assert isinstance(attack, OutOfOrderEventAttack)
    assert attack.source_sequence == 2
    assert attack.target_sequence == 1


def test_out_of_order_requires_source_sequence() -> None:
    simulation = make_simulation()

    with pytest.raises(
        ValueError,
        match="source_sequence is required for out_of_order attacks",
    ):
        _build_attack(
            simulation,
            AttackRequest(
                attack_type="out_of_order",
                target_sequence=1,
            ),
        )


def test_other_attack_types_do_not_require_source_sequence() -> None:
    simulation = make_simulation()

    attack = _build_attack(
        simulation,
        AttackRequest(
            attack_type="duplicate",
            target_sequence=0,
        ),
    )

    assert attack.target_sequence == 0
