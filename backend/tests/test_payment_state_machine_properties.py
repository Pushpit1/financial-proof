from uuid import uuid4

import pytest

from app.domain.enums.payment import (
    OrderState,
    PaymentEvent,
    PaymentState,
)
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.services.payment_state_machine import (
    InvalidOrderTransition,
    InvalidPaymentTransition,
    OrderStateMachine,
    PaymentStateMachine,
)

PAYMENT_STATES = tuple(PaymentState)
ORDER_STATES = tuple(OrderState)
EVENTS = tuple(PaymentEvent)


def make_payment(state: PaymentState) -> Payment:
    return Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
        state=state,
    )


def make_order(state: OrderState) -> PaymentOrder:
    return PaymentOrder(
        amount_minor=1000,
        currency="INR",
        state=state,
    )


def test_payment_transition_table_is_total_over_declared_inputs() -> None:
    valid = PaymentStateMachine._TRANSITIONS

    for state in PAYMENT_STATES:
        for event in EVENTS:
            key = (state, event)

            if key in valid:
                result = PaymentStateMachine.transition(
                    make_payment(state),
                    event,
                )
                assert result.state is valid[key]
            else:
                with pytest.raises(InvalidPaymentTransition):
                    PaymentStateMachine.transition(
                        make_payment(state),
                        event,
                    )


def test_order_transition_table_is_total_over_declared_inputs() -> None:
    valid = OrderStateMachine._TRANSITIONS

    for state in ORDER_STATES:
        for event in EVENTS:
            key = (state, event)

            if key in valid:
                result = OrderStateMachine.transition(
                    make_order(state),
                    event,
                )
                assert result.state is valid[key]
            else:
                with pytest.raises(InvalidOrderTransition):
                    OrderStateMachine.transition(
                        make_order(state),
                        event,
                    )


def test_invalid_payment_event_never_mutates_original() -> None:
    for state in PAYMENT_STATES:
        payment = make_payment(state)
        original_state = payment.state

        for event in EVENTS:
            if (state, event) in PaymentStateMachine._TRANSITIONS:
                continue

            with pytest.raises(InvalidPaymentTransition):
                PaymentStateMachine.transition(payment, event)

            assert payment.state is original_state


def test_invalid_order_event_never_mutates_original() -> None:
    for state in ORDER_STATES:
        order = make_order(state)
        original_state = order.state

        for event in EVENTS:
            if (state, event) in OrderStateMachine._TRANSITIONS:
                continue

            with pytest.raises(InvalidOrderTransition):
                OrderStateMachine.transition(order, event)

            assert order.state is original_state


def test_valid_payment_transition_preserves_identity_and_financial_data() -> None:
    for (state, event), expected_state in PaymentStateMachine._TRANSITIONS.items():
        payment = make_payment(state)

        result = PaymentStateMachine.transition(payment, event)

        assert result.id == payment.id
        assert result.order_id == payment.order_id
        assert result.amount_minor == payment.amount_minor
        assert result.currency == payment.currency
        assert result.state is expected_state


def test_valid_order_transition_preserves_identity_and_financial_data() -> None:
    for (state, event), expected_state in OrderStateMachine._TRANSITIONS.items():
        order = make_order(state)

        result = OrderStateMachine.transition(order, event)

        assert result.id == order.id
        assert result.amount_minor == order.amount_minor
        assert result.currency == order.currency
        assert result.state is expected_state


def test_payment_terminal_states_have_no_valid_outgoing_transition() -> None:
    terminal_states = {
        state
        for state in PAYMENT_STATES
        if not any(
            from_state is state
            for from_state, _event in PaymentStateMachine._TRANSITIONS
        )
    }

    for state in terminal_states:
        for event in EVENTS:
            with pytest.raises(InvalidPaymentTransition):
                PaymentStateMachine.transition(
                    make_payment(state),
                    event,
                )


def test_order_terminal_states_have_no_valid_outgoing_transition() -> None:
    terminal_states = {
        state
        for state in ORDER_STATES
        if not any(
            from_state is state
            for from_state, _event in OrderStateMachine._TRANSITIONS
        )
    }

    for state in terminal_states:
        for event in EVENTS:
            with pytest.raises(InvalidOrderTransition):
                OrderStateMachine.transition(
                    make_order(state),
                    event,
                )


def test_payment_transition_is_deterministic() -> None:
    for (state, event), expected_state in PaymentStateMachine._TRANSITIONS.items():
        first = PaymentStateMachine.transition(
            make_payment(state),
            event,
        )
        second = PaymentStateMachine.transition(
            make_payment(state),
            event,
        )

        assert first.state is expected_state
        assert second.state is expected_state
        assert first.state == second.state


def test_order_transition_is_deterministic() -> None:
    for (state, event), expected_state in OrderStateMachine._TRANSITIONS.items():
        first = OrderStateMachine.transition(
            make_order(state),
            event,
        )
        second = OrderStateMachine.transition(
            make_order(state),
            event,
        )

        assert first.state is expected_state
        assert second.state is expected_state
        assert first.state == second.state
