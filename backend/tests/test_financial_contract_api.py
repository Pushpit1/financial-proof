"""Integration tests for the financial contract API."""

from uuid import uuid4


def test_create_contract(client) -> None:
    response = client.post(
        "/contracts",
        json={
            "name": "Income Verification Contract",
            "version": 1,
            "minimum_confidence": "0.80",
            "minimum_supported_claim_ratio": "0.90",
            "required_claim_types": [
                "income",
                "employment",
            ],
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["name"] == "Income Verification Contract"
    assert body["version"] == 1
    assert body["minimum_confidence"] == "0.80"
    assert body["minimum_supported_claim_ratio"] == "0.90"
    assert body["required_claim_types"] == [
        "income",
        "employment",
    ]
    assert body["id"]


def test_get_contract_by_id(client) -> None:
    create_response = client.post(
        "/contracts",
        json={
            "name": "ID Lookup Contract",
            "version": 1,
            "minimum_confidence": "0.75",
            "minimum_supported_claim_ratio": "0.85",
            "required_claim_types": ["income"],
        },
    )

    assert create_response.status_code == 201

    contract_id = create_response.json()["id"]

    response = client.get(f"/contracts/{contract_id}")

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == contract_id
    assert body["name"] == "ID Lookup Contract"
    assert body["version"] == 1


def test_get_contract_by_name_and_version(client) -> None:
    create_response = client.post(
        "/contracts",
        json={
            "name": "Version Lookup Contract",
            "version": 2,
            "minimum_confidence": "0.85",
            "minimum_supported_claim_ratio": "0.95",
            "required_claim_types": ["income"],
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        "/contracts/Version%20Lookup%20Contract/2"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["name"] == "Version Lookup Contract"
    assert body["version"] == 2


def test_get_contract_returns_404_when_missing(client) -> None:
    contract_id = uuid4()

    response = client.get(f"/contracts/{contract_id}")

    assert response.status_code == 404


def test_get_contract_version_returns_404_when_missing(client) -> None:
    response = client.get(
        "/contracts/Does%20Not%20Exist/99"
    )

    assert response.status_code == 404


def test_create_contract_rejects_invalid_confidence(client) -> None:
    response = client.post(
        "/contracts",
        json={
            "name": "Invalid Confidence Contract",
            "version": 1,
            "minimum_confidence": "1.50",
            "minimum_supported_claim_ratio": "0.90",
            "required_claim_types": ["income"],
        },
    )

    assert response.status_code == 422


def test_create_contract_rejects_invalid_claim_ratio(client) -> None:
    response = client.post(
        "/contracts",
        json={
            "name": "Invalid Ratio Contract",
            "version": 1,
            "minimum_confidence": "0.80",
            "minimum_supported_claim_ratio": "-0.10",
            "required_claim_types": ["income"],
        },
    )

    assert response.status_code == 422

def test_create_contract_rejects_duplicate_version(client) -> None:
    payload = {
        "name": "API Duplicate Contract",
        "version": 1,
        "minimum_confidence": "0.80",
        "minimum_supported_claim_ratio": "0.90",
        "required_claim_types": ["income"],
    }

    first_response = client.post(
        "/contracts",
        json=payload,
    )

    assert first_response.status_code == 201

    duplicate_response = client.post(
        "/contracts",
        json={
            **payload,
            "minimum_confidence": "0.95",
            "minimum_supported_claim_ratio": "0.99",
            "required_claim_types": ["employment"],
        },
    )

    assert duplicate_response.status_code == 409

    body = duplicate_response.json()

    assert "detail" in body
