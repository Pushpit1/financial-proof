"""Integration tests for the financial simulation API."""

from uuid import UUID, uuid4

from fastapi.testclient import TestClient


def _simulation_payload() -> dict:
    return {
        "seed": 42,
        "amount_minor": 1000,
        "currency": "INR",
        "events": [
            {
                "event": "authorize",
                "occurred_at": "2026-09-02T10:00:00+00:00",
            },
            {
                "event": "capture",
                "occurred_at": "2026-09-02T10:00:01+00:00",
            },
        ],
    }


def test_create_simulation_returns_completed_baseline(
    client: TestClient,
) -> None:
    response = client.post(
        "/simulations",
        json=_simulation_payload(),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"]
    assert UUID(body["id"])
    assert body["seed"] == 42
    assert body["amount_minor"] == 1000
    assert body["currency"] == "INR"
    assert len(body["events"]) == 2

    assert body["events"][0]["sequence"] == 0
    assert body["events"][0]["event"] == "authorize"
    assert body["events"][1]["sequence"] == 1
    assert body["events"][1]["event"] == "capture"

    assert body["result"]["simulation_id"] == body["id"]
    assert body["result"]["seed"] == 42
    assert body["result"]["final_payment_state"] == "captured"
    assert body["result"]["final_order_state"] == "captured"
    assert len(body["result"]["trace"]) == 2
    assert len(body["result"]["snapshots"]) == 2


def test_get_simulation_returns_same_deterministic_result(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/simulations",
        json=_simulation_payload(),
    )

    assert create_response.status_code == 201

    simulation_id = create_response.json()["id"]

    response = client.get(f"/simulations/{simulation_id}")

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == simulation_id
    assert body["seed"] == 42
    assert body["amount_minor"] == 1000
    assert body["currency"] == "INR"
    assert body["result"]["simulation_id"] == simulation_id
    assert body["result"]["final_payment_state"] == "captured"
    assert body["result"]["final_order_state"] == "captured"


def test_get_simulation_returns_404_for_missing_simulation(
    client: TestClient,
) -> None:
    response = client.get(f"/simulations/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Simulation not found"


def test_execute_retry_attack_returns_baseline_and_adversarial_results(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/simulations",
        json=_simulation_payload(),
    )

    assert create_response.status_code == 201

    simulation_id = create_response.json()["id"]

    response = client.post(
        f"/simulations/{simulation_id}/attacks",
        json={
            "attack_type": "retry",
            "target_sequence": 0,
            "retry_count": 3,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["simulation_id"] == simulation_id
    assert body["attack_count"] == 1
    assert body["applied_components"] == ["RetryScenario"]

    assert len(body["outcomes"]) == 1
    assert body["outcomes"][0]["component_type"] == "RetryScenario"
    assert body["outcomes"][0]["target_sequence"] == 0
    assert body["outcomes"][0]["status"] == "applied"

    assert body["baseline"]["simulation_id"] == simulation_id
    assert body["adversarial"]["simulation_id"] == simulation_id
    assert body["baseline"]["final_payment_state"] == "captured"
    assert body["adversarial"]["final_payment_state"] == "captured"


def test_execute_attack_returns_404_for_missing_simulation(
    client: TestClient,
) -> None:
    response = client.post(
        f"/simulations/{uuid4()}/attacks",
        json={
            "attack_type": "retry",
            "target_sequence": 0,
            "retry_count": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Simulation not found"


def test_create_simulation_rejects_invalid_amount(
    client: TestClient,
) -> None:
    payload = _simulation_payload()
    payload["amount_minor"] = 0

    response = client.post(
        "/simulations",
        json=payload,
    )

    assert response.status_code == 422


def test_create_simulation_rejects_invalid_currency(
    client: TestClient,
) -> None:
    payload = _simulation_payload()
    payload["currency"] = "IN"

    response = client.post(
        "/simulations",
        json=payload,
    )

    assert response.status_code == 422


def test_retry_attack_requires_retry_count(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/simulations",
        json=_simulation_payload(),
    )

    assert create_response.status_code == 201

    simulation_id = create_response.json()["id"]

    response = client.post(
        f"/simulations/{simulation_id}/attacks",
        json={
            "attack_type": "retry",
            "target_sequence": 0,
        },
    )

    assert response.status_code == 422
    assert "retry_count is required" in response.json()["detail"]

def test_duplicate_attack_returns_validation_error_for_invalid_transition(
    client,
) -> None:
    create_response = client.post(
        "/simulations",
        json={
            "seed": 42,
            "amount_minor": 10000,
            "currency": "INR",
            "events": [
                {
                    "event": "authorize",
                    "occurred_at": "2026-09-02T10:00:00Z",
                },
                {
                    "event": "capture",
                    "occurred_at": "2026-09-02T10:00:01Z",
                },
            ],
        },
    )

    assert create_response.status_code == 201

    simulation_id = create_response.json()["id"]

    response = client.post(
        f"/simulations/{simulation_id}/attacks",
        json={
            "attack_type": "duplicate",
            "target_sequence": 0,
        },
    )

    assert response.status_code == 422
    assert "authorize" in response.json()["detail"].lower()
