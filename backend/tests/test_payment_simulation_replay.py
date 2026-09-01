from datetime import UTC, datetime

from app.domain.enums.payment import OrderState, PaymentEvent, PaymentState
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.services.payment_simulation_replay import PaymentSimulationReplay


def make_order() -> PaymentOrder:
    return PaymentOrder(
        amount_minor=1000,
        currency="INR",
        state=OrderState.CREATED,
    )


def make_payment(order_id) -> Payment:
    return Payment(
        order_id=order_id,
        amount_minor=1000,
        currency="INR",
        state=PaymentState.CREATED,
    )


def test_replay_reconstructs_same_final_state() -> None:
    start = datetime(2026, 8, 31, tzinfo=UTC)
    order = make_order()

    simulation = PaymentSimulation(
        seed=42,
        initial_payment=make_payment(order.id),
        initial_order=order,
        events=(
            SimulationEvent(
                sequence=0,
                event=PaymentEvent.AUTHORIZE,
                occurred_at=start,
            ),
            SimulationEvent(
                sequence=1,
                event=PaymentEvent.CAPTURE,
                occurred_at=start.replace(second=1),
            ),
        ),
    )

    first = PaymentSimulationReplay.replay(simulation)
    second = PaymentSimulationReplay.replay(simulation)

    assert first.final_payment == second.final_payment
    assert first.final_order == second.final_order
    assert first.trace == second.trace
    assert first.snapshots == second.snapshots

