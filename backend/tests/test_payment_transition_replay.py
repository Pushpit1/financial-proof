from uuid import uuid4

import pytest

from app.domain.enums.payment import (
    PaymentEvent,
    PaymentState,
)
from app.domain.models.payment import Payment
from app.domain.models.payment_transition import PaymentTransition
from app.domain.services.payment_transition_recorder import (
    PaymentTransitionRecorder,
)
from app.domain.services.payment_transition_replay import (
    PaymentTransitionReplayService,
    ReplayConsistencyError,
)


def test_transition_replay_reconstructs_final_state() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    authorized, first = PaymentTransitionRecorder.apply(
        payment,
        PaymentEvent.AUTHORIZE,
    )

    _, second = PaymentTransitionRecorder.apply(
        authorized,
        PaymentEvent.CAPTURE,
    )

    result = PaymentTransitionReplayService.replay(
        payment,
        (first, second),
    )

    assert result.state == PaymentState.CAPTURED
    assert result.id == payment.id


def test_transition_replay_rejects_wrong_payment() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    _, transition = PaymentTransitionRecorder.apply(
        payment,
        PaymentEvent.AUTHORIZE,
    )

    foreign_payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    foreign_transition = PaymentTransition(
        payment_id=foreign_payment.id,
        from_state=transition.from_state,
        event=transition.event,
        to_state=transition.to_state,
    )

    with pytest.raises(ReplayConsistencyError):
        PaymentTransitionReplayService.replay(
            payment,
            (foreign_transition,),
        )


def test_transition_replay_rejects_wrong_from_state() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    transition = PaymentTransition(
        payment_id=payment.id,
        from_state=PaymentState.CAPTURED,
        event=PaymentEvent.AUTHORIZE,
        to_state=PaymentState.AUTHORIZED,
    )

    with pytest.raises(ReplayConsistencyError):
        PaymentTransitionReplayService.replay(
            payment,
            (transition,),
        )


def test_transition_replay_rejects_tampered_to_state() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    transition = PaymentTransition(
        payment_id=payment.id,
        from_state=PaymentState.CREATED,
        event=PaymentEvent.AUTHORIZE,
        to_state=PaymentState.FAILED,
    )

    with pytest.raises(ReplayConsistencyError):
        PaymentTransitionReplayService.replay(
            payment,
            (transition,),
        )


def test_transition_replay_is_deterministic() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    _, transition = PaymentTransitionRecorder.apply(
        payment,
        PaymentEvent.AUTHORIZE,
    )

    first = PaymentTransitionReplayService.replay(
        payment,
        (transition,),
    )

    second = PaymentTransitionReplayService.replay(
        payment,
        (transition,),
    )

    assert first == second
