from datetime import UTC, datetime

from fastapi import status


def _baseline_payload() -> dict:
    return {
        "seed": 42,
        "amount_minor": 10000,
        "currency": "INR",
        "events": [
            {
                "event": "authorize",
                "occurred_at": datetime(
                    2026, 1, 1, tzinfo=UTC
                ).isoformat(),
            },
            {
                "event": "capture",
                "occurred_at": datetime(
                    2026, 1, 1, 0, 0, 1, tzinfo=UTC
                ).isoformat(),
            },
            {
                "event": "refund",
                "occurred_at": datetime(
                    2026, 1, 1, 0, 0, 2, tzinfo=UTC
                ).isoformat(),
            },
        ],
    }


def test_counterexample_endpoint_shrinks_failed_out_of_order_attack(
    client,
) -> None:
    create = client.post(
        "/simulations",
        json=_baseline_payload(),
    )

    assert create.status_code == status.HTTP_201_CREATED

    simulation_id = create.json()["id"]

    response = client.post(
        f"/simulations/{simulation_id}/counterexample",
        json={
            "attack_type": "out_of_order",
            "source_sequence": 2,
            "target_sequence": 1,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    body = response.json()

    assert body["simulation_id"] == simulation_id
    assert body["violation_code"] == "INVALID_PAYMENT_TRANSITION"
    assert body["original_event_count"] == 3
    assert body["minimized_event_count"] == 2
    assert [event["event"] for event in body["events"]] == [
        "authorize",
        "refund",
    ]


def test_counterexample_endpoint_rejects_non_failing_attack(
    client,
) -> None:
    create = client.post(
        "/simulations",
        json=_baseline_payload(),
    )

    assert create.status_code == status.HTTP_201_CREATED

    simulation_id = create.json()["id"]

    response = client.post(
        f"/simulations/{simulation_id}/counterexample",
        json={
            "attack_type": "retry",
            "target_sequence": 1,
            "retry_count": 2,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_counterexample_endpoint_rejects_unknown_simulation(
    client,
) -> None:
    from uuid import uuid4

    response = client.post(
        f"/simulations/{uuid4()}/counterexample",
        json={
            "attack_type": "out_of_order",
            "source_sequence": 2,
            "target_sequence": 1,
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
