from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.routes.financial_simulation import _simulations
from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def _simulation_payload() -> dict:
    timestamp = datetime(2026, 9, 4, 12, 0, 0, tzinfo=UTC)

    return {
        "seed": 207,
        "amount_minor": 25000,
        "currency": "USD",
        "events": [
            {
                "event": "authorize",
                "occurred_at": timestamp.isoformat(),
            },
            {
                "event": "capture",
                "occurred_at": timestamp.replace(second=1).isoformat(),
            },
            {
                "event": "refund",
                "occurred_at": timestamp.replace(second=2).isoformat(),
            },
        ],
    }


def test_out_of_order_invalid_replay_is_returned_as_attack_failure() -> None:
    _simulations.clear()
    client = _client()

    create_response = client.post(
        "/simulations",
        json=_simulation_payload(),
    )

    assert create_response.status_code == 201

    simulation = create_response.json()
    assert simulation["result"]["final_payment_state"] == "refunded"

    response = client.post(
        f"/simulations/{simulation['id']}/attacks",
        json={
            "attack_type": "out_of_order",
            "source_sequence": 2,
            "target_sequence": 1,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["adversarial_status"] == "failed"
    assert body["adversarial"] is None

    assert body["failure"] == {
        "failure_type": "InvalidPaymentTransition",
        "message": (
            "Cannot apply 'refund' to payment "
            "in state 'authorized'."
        ),
    }

    assert body["baseline"]["final_payment_state"] == "refunded"
    assert body["attack_count"] == 1
    assert body["applied_components"] == ["OutOfOrderEventAttack"]


def test_missing_out_of_order_source_sequence_remains_validation_error() -> None:
    _simulations.clear()
    client = _client()

    create_response = client.post(
        "/simulations",
        json=_simulation_payload(),
    )

    assert create_response.status_code == 201

    simulation = create_response.json()

    response = client.post(
        f"/simulations/{simulation['id']}/attacks",
        json={
            "attack_type": "out_of_order",
            "target_sequence": 1,
        },
    )

    assert response.status_code == 422
    assert "source_sequence is required" in response.json()["detail"]


def test_successful_adversarial_replay_returns_completed_result() -> None:
    _simulations.clear()
    client = _client()

    create_response = client.post(
        "/simulations",
        json=_simulation_payload(),
    )

    assert create_response.status_code == 201

    simulation = create_response.json()

    response = client.post(
        f"/simulations/{simulation['id']}/attacks",
        json={
            "attack_type": "retry",
            "target_sequence": 1,
            "retry_count": 2,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["adversarial_status"] == "completed"
    assert body["failure"] is None
    assert body["adversarial"] is not None
    assert body["adversarial"]["final_payment_state"] == "refunded"
