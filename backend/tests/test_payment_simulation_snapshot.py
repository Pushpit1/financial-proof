from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.enums.payment import OrderState, PaymentEvent, PaymentState
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation_snapshot import SimulationSnapshot


def make_payment() -> Payment:
    return Payment(
        amount_minor=1000,
        currency="INR",
        state=PaymentState.CREATED,
        order_id=uuid4(),
    )


def make_order() -> PaymentOrder:
    return PaymentOrder(
        amount_minor=1000,
        currency="INR",
        state=OrderState.CREATED,
    )


def test_snapshot_is_immutable() -> None:
    snapshot = SimulationSnapshot(
        sequence=0,
        event=PaymentEvent.AUTHORIZE,
        occurred_at=datetime(2026, 8, 31, tzinfo=UTC),
        payment=make_payment(),
        order=make_order(),
    )

    with pytest.raises(AttributeError):
        snapshot.sequence = 1  # type: ignore[misc]


def test_snapshot_rejects_negative_sequence() -> None:
    with pytest.raises(ValueError, match="Snapshot sequence cannot be negative"):
        SimulationSnapshot(
            sequence=-1,
            event=None,
            occurred_at=datetime(2026, 8, 31, tzinfo=UTC),
            payment=make_payment(),
            order=make_order(),
        )


def test_snapshot_can_represent_initial_state() -> None:
    snapshot = SimulationSnapshot(
        sequence=0,
        event=None,
        occurred_at=datetime(2026, 8, 31, tzinfo=UTC),
        payment=make_payment(),
        order=make_order(),
    )

    assert snapshot.event is None
    assert snapshot.sequence == 0
