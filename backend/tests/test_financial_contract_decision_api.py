"""Integration tests for financial contract decision API."""

from uuid import uuid4


def create_contract(client) -> str:
    response = client.post(
        "/contracts",
        json={
            "name": "Decision API Contract",
            "version": 1,
            "minimum_confidence": "0.80",
            "minimum_supported_claim_ratio": "0.90",
            "required_claim_types": ["income"],
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_evaluate_contract_persists_passing_decision(client) -> None:
    contract_id = create_contract(client)

    response = client.post(
        f"/contracts/{contract_id}/decisions",
        json={
            "context": {},
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"]
    assert body["contract_id"] == contract_id
    assert body["passed"] is True
    assert body["reason_codes"] == []
    assert body["violation_count"] == 0
    assert body["evaluated_at"]


def test_evaluate_contract_returns_404_for_missing_contract(
    client,
) -> None:
    contract_id = str(uuid4())

    response = client.post(
        f"/contracts/{contract_id}/decisions",
        json={
            "context": {},
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == (
        f"Financial contract {contract_id} was not found."
    )


def test_evaluate_contract_accepts_context(client) -> None:
    contract_id = create_contract(client)

    response = client.post(
        f"/contracts/{contract_id}/decisions",
        json={
            "context": {
                "monthly_income": "75000",
                "employment_status": "employed",
            },
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["contract_id"] == contract_id
    assert body["passed"] is True
    assert body["violation_count"] == 0


def test_evaluate_contract_rejects_invalid_request_shape(client) -> None:
    contract_id = create_contract(client)

    response = client.post(
        f"/contracts/{contract_id}/decisions",
        json={
            "context": "not-an-object",
        },
    )

    assert response.status_code == 422


def test_evaluate_contract_generates_unique_decisions(client) -> None:
    contract_id = create_contract(client)

    first_response = client.post(
        f"/contracts/{contract_id}/decisions",
        json={"context": {}},
    )
    second_response = client.post(
        f"/contracts/{contract_id}/decisions",
        json={"context": {}},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first = first_response.json()
    second = second_response.json()

    assert first["id"] != second["id"]
    assert first["contract_id"] == contract_id
    assert second["contract_id"] == contract_id

def test_list_contract_decisions_returns_persisted_history(client) -> None:
    contract_id = create_contract(client)

    first_response = client.post(
        f"/contracts/{contract_id}/decisions",
        json={"context": {}},
    )
    second_response = client.post(
        f"/contracts/{contract_id}/decisions",
        json={"context": {}},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first = first_response.json()
    second = second_response.json()

    response = client.get(
        f"/contracts/{contract_id}/decisions",
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 2
    assert body[0]["id"] == first["id"]
    assert body[1]["id"] == second["id"]

    assert body[0]["contract_id"] == contract_id
    assert body[1]["contract_id"] == contract_id
    assert body[0]["passed"] is True
    assert body[1]["passed"] is True


def test_list_contract_decisions_returns_empty_history_for_new_contract(
    client,
) -> None:
    contract_id = create_contract(client)

    response = client.get(
        f"/contracts/{contract_id}/decisions",
    )

    assert response.status_code == 200
    assert response.json() == []

def test_list_contract_decisions_supports_limit_and_offset(client) -> None:
    contract_id = create_contract(client)

    created = []

    for _ in range(5):
        response = client.post(
            f"/contracts/{contract_id}/decisions",
            json={"context": {}},
        )
        assert response.status_code == 201
        created.append(response.json())

    response = client.get(
        f"/contracts/{contract_id}/decisions",
        params={
            "limit": 2,
            "offset": 1,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 2
    assert body[0]["id"] == created[1]["id"]
    assert body[1]["id"] == created[2]["id"]


def test_list_contract_decisions_defaults_to_first_page(client) -> None:
    contract_id = create_contract(client)

    for _ in range(3):
        response = client.post(
            f"/contracts/{contract_id}/decisions",
            json={"context": {}},
        )
        assert response.status_code == 201

    response = client.get(
        f"/contracts/{contract_id}/decisions",
    )

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_list_contract_decisions_rejects_invalid_limit(client) -> None:
    contract_id = create_contract(client)

    too_small = client.get(
        f"/contracts/{contract_id}/decisions",
        params={"limit": 0},
    )
    too_large = client.get(
        f"/contracts/{contract_id}/decisions",
        params={"limit": 101},
    )

    assert too_small.status_code == 422
    assert too_large.status_code == 422


def test_list_contract_decisions_rejects_negative_offset(client) -> None:
    contract_id = create_contract(client)

    response = client.get(
        f"/contracts/{contract_id}/decisions",
        params={"offset": -1},
    )

    assert response.status_code == 422


def test_list_contract_decisions_preserves_missing_contract_404(client) -> None:
    contract_id = str(uuid4())

    response = client.get(
        f"/contracts/{contract_id}/decisions",
        params={
            "limit": 10,
            "offset": 0,
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        f"Financial contract {contract_id} was not found."
    )
