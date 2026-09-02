"""Tests for the natural-language financial contract compiler API."""

from fastapi.testclient import TestClient


def test_compile_contract_returns_compiled_contract(
    client: TestClient,
) -> None:
    response = client.post(
        "/contracts/compile",
        json={
            "source_text": "Refund Policy",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["source_text"] == "Refund Policy"
    assert body["contract"]["name"] == "Refund Policy"
    assert body["contract"]["version"] == 1
    assert body["contract"]["minimum_confidence"] == "0"
    assert body["contract"]["minimum_supported_claim_ratio"] == "1"
    assert body["contract"]["required_claim_types"] == []


def test_compile_contract_normalizes_source_text(
    client: TestClient,
) -> None:
    response = client.post(
        "/contracts/compile",
        json={
            "source_text": "  Refund Policy  ",
        },
    )

    assert response.status_code == 200
    assert response.json()["source_text"] == "Refund Policy"


def test_compile_contract_rejects_blank_source_text(
    client: TestClient,
) -> None:
    response = client.post(
        "/contracts/compile",
        json={
            "source_text": "",
        },
    )

    assert response.status_code == 422


def test_compile_contract_rejects_unknown_fields(
    client: TestClient,
) -> None:
    response = client.post(
        "/contracts/compile",
        json={
            "source_text": "Refund Policy",
            "unexpected": True,
        },
    )

    assert response.status_code == 422
