from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.application.services.financial_proof import (
    FinancialProofApplicationService,
)
from app.core.config import get_settings
from app.db.unit_of_work import FinancialUnitOfWork
from app.domain.enums.financial import EvidenceType
from app.domain.models.financial import Evidence, FinancialProof


def test_root(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200

    body = response.json()

    assert body["name"] == "Financial Proof"
    assert body["version"] == "0.1.0"


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_correlation_id(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"]


def test_custom_correlation_id(client: TestClient) -> None:
    correlation_id = "fp-test-123"

    response = client.get(
        "/health",
        headers={"X-Correlation-ID": correlation_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == correlation_id

def test_get_proof_returns_complete_aggregate(
    client: TestClient,
    db: Session,
) -> None:
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(db)
    )

    proof = FinancialProof(subject="Applicant")
    evidence = Evidence(
        evidence_type=EvidenceType.PAYSLIP,
        source_name="Employer",
        received_at=date(2026, 8, 28),
    )

    service.create_proof(
        proof,
        [],
        [evidence],
        [],
    )

    response = client.get(f"/proofs/{proof.id}")

    assert response.status_code == 200

    body = response.json()

    assert body["proof"]["id"] == str(proof.id)
    assert body["proof"]["subject"] == "Applicant"
    assert body["proof"]["status"] == "draft"
    assert body["claims"] == []
    assert len(body["evidence"]) == 1
    assert body["evidence"][0]["id"] == str(evidence.id)


def test_get_proof_returns_404_for_missing_proof(
    client: TestClient,
) -> None:
    from uuid import uuid4

    response = client.get(f"/proofs/{uuid4()}")

    assert response.status_code == 404


def test_create_proof_defaults_empty_collections(
    client: TestClient,
) -> None:
    response = client.post(
        "/proofs",
        json={"subject": "Applicant"},
    )

    assert response.status_code == 201

    body = response.json()

    assert body["proof"]["subject"] == "Applicant"
    assert body["claims"] == []
    assert body["evidence"] == []
    assert body["evidence_links"] == []


def test_create_proof_rejects_confidence_above_one(
    client: TestClient,
) -> None:
    response = client.post(
        "/proofs",
        json={
            "subject": "Applicant",
            "claims": [
                {
                    "claim_type": "income",
                    "subject": "Monthly salary",
                    "confidence": "1.01",
                }
            ],
        },
    )

    assert response.status_code == 422


def test_create_proof_rejects_negative_confidence(
    client: TestClient,
) -> None:
    response = client.post(
        "/proofs",
        json={
            "subject": "Applicant",
            "claims": [
                {
                    "claim_type": "income",
                    "subject": "Monthly salary",
                    "confidence": "-0.01",
                }
            ],
        },
    )

    assert response.status_code == 422


def test_create_proof_rejects_amount_without_currency(
    client: TestClient,
) -> None:
    response = client.post(
        "/proofs",
        json={
            "subject": "Applicant",
            "claims": [
                {
                    "claim_type": "income",
                    "subject": "Monthly salary",
                    "amount": "5000.00",
                }
            ],
        },
    )

    assert response.status_code == 422


def test_create_proof_accepts_claim_without_amount(
    client: TestClient,
) -> None:
    response = client.post(
        "/proofs",
        json={
            "subject": "Applicant",
            "claims": [
                {
                    "claim_type": "income",
                    "subject": "Monthly salary",
                    "confidence": "0.80",
                    "confidence_level": "high",
                }
            ],
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert len(body["claims"]) == 1
    assert body["claims"][0]["amount"] is None
    assert body["claims"][0]["currency"] is None


def test_create_proof_accepts_explicit_ids(
    client: TestClient,
) -> None:
    proof_claim_id = "31111111-1111-4111-8111-111111111111"
    evidence_id = "32222222-2222-4222-8222-222222222222"

    response = client.post(
        "/proofs",
        json={
            "subject": "Applicant",
            "claims": [
                {
                    "id": proof_claim_id,
                    "claim_type": "income",
                    "subject": "Monthly salary",
                }
            ],
            "evidence": [
                {
                    "id": evidence_id,
                    "evidence_type": "payslip",
                    "source_name": "Employer",
                    "received_at": "2026-08-28",
                }
            ],
            "evidence_links": [
                {
                    "claim_id": proof_claim_id,
                    "evidence_id": evidence_id,
                    "explanation": "Employer payslip supports salary claim.",
                }
            ],
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["claims"][0]["id"] == proof_claim_id
    assert body["evidence"][0]["id"] == evidence_id
    assert body["evidence_links"][0]["claim_id"] == proof_claim_id
    assert body["evidence_links"][0]["evidence_id"] == evidence_id


def test_create_proof_rejects_invalid_evidence_type(
    client: TestClient,
) -> None:
    response = client.post(
        "/proofs",
        json={
            "subject": "Applicant",
            "evidence": [
                {
                    "evidence_type": "not_real",
                    "source_name": "Employer",
                    "received_at": "2026-08-28",
                }
            ],
        },
    )

    assert response.status_code == 422


def test_create_proof_rejects_invalid_verification_status(
    client: TestClient,
) -> None:
    response = client.post(
        "/proofs",
        json={
            "subject": "Applicant",
            "claims": [
                {
                    "claim_type": "income",
                    "subject": "Monthly salary",
                    "verification_status": "not_real",
                }
            ],
        },
    )

    assert response.status_code == 422


def test_create_proof_rejects_invalid_confidence_level(
    client: TestClient,
) -> None:
    response = client.post(
        "/proofs",
        json={
            "subject": "Applicant",
            "claims": [
                {
                    "claim_type": "income",
                    "subject": "Monthly salary",
                    "confidence_level": "not_real",
                }
            ],
        },
    )

    assert response.status_code == 422


def test_create_proof_rejects_malformed_uuid(
    client: TestClient,
) -> None:
    response = client.post(
        "/proofs",
        json={
            "subject": "Applicant",
            "claims": [
                {
                    "id": "not-a-uuid",
                    "claim_type": "income",
                    "subject": "Monthly salary",
                }
            ],
        },
    )

    assert response.status_code == 422


def test_create_proof_rejects_invalid_received_date(
    client: TestClient,
) -> None:
    response = client.post(
        "/proofs",
        json={
            "subject": "Applicant",
            "evidence": [
                {
                    "evidence_type": "payslip",
                    "source_name": "Employer",
                    "received_at": "not-a-date",
                }
            ],
        },
    )

    assert response.status_code == 422



def test_evaluate_proof_returns_ready_for_valid_claims(
    client: TestClient,
) -> None:
    response = client.post(
        "/proofs",
        json={
            "subject": "Applicant",
            "claims": [
                {
                    "claim_type": "income",
                    "subject": "Monthly salary",
                    "confidence": "0.90",
                    "verification_status": "verified",
                },
                {
                    "claim_type": "income",
                    "subject": "Annual bonus",
                    "confidence": "0.70",
                    "verification_status": "verified",
                },
            ],
        },
    )

    assert response.status_code == 201

    proof_id = response.json()["proof"]["id"]

    response = client.post(f"/proofs/{proof_id}/evaluate")

    assert response.status_code == 200

    body = response.json()

    assert body["proof"]["id"] == proof_id
    assert body["proof"]["status"] == "ready"
    assert body["proof"]["overall_confidence"] == "0.8000"
    assert len(body["claims"]) == 2


def test_evaluate_proof_returns_ready_for_empty_proof(
    client: TestClient,
) -> None:
    response = client.post(
        "/proofs",
        json={"subject": "Applicant"},
    )

    assert response.status_code == 201

    proof_id = response.json()["proof"]["id"]

    response = client.post(f"/proofs/{proof_id}/evaluate")

    assert response.status_code == 200

    body = response.json()

    assert body["proof"]["status"] == "ready"
    assert body["proof"]["overall_confidence"] == "0.0000"


def test_evaluate_proof_returns_invalid_for_contradicted_claim(
    client: TestClient,
) -> None:
    response = client.post(
        "/proofs",
        json={
            "subject": "Applicant",
            "claims": [
                {
                    "claim_type": "income",
                    "subject": "Verified income",
                    "confidence": "0.90",
                    "verification_status": "verified",
                },
                {
                    "claim_type": "income",
                    "subject": "Contradicted income",
                    "confidence": "0.80",
                    "verification_status": "contradicted",
                },
            ],
        },
    )

    assert response.status_code == 201

    proof_id = response.json()["proof"]["id"]

    response = client.post(f"/proofs/{proof_id}/evaluate")

    assert response.status_code == 200

    body = response.json()

    assert body["proof"]["status"] == "invalid"
    assert body["proof"]["overall_confidence"] == "0.8500"


def test_evaluate_proof_returns_404_for_missing_proof(
    client: TestClient,
) -> None:
    from uuid import uuid4

    response = client.post(f"/proofs/{uuid4()}/evaluate")

    assert response.status_code == 404

def test_evaluate_proof_persists_result(client: TestClient) -> None:
    response = client.post(
        "/proofs",
        json={
            "subject": "Applicant",
            "claims": [
                {
                    "claim_type": "income",
                    "subject": "Monthly income",
                    "confidence": "0.60",
                    "verification_status": "verified",
                },
                {
                    "claim_type": "income",
                    "subject": "Annual income",
                    "confidence": "0.80",
                    "verification_status": "verified",
                },
            ],
        },
    )

    assert response.status_code == 201

    proof_id = response.json()["proof"]["id"]

    response = client.post(
        f"/proofs/{proof_id}/evaluate"
    )

    assert response.status_code == 200

    response = client.get(
        f"/proofs/{proof_id}"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["proof"]["status"] == "ready"
    assert body["proof"]["overall_confidence"] == "0.7000"

def test_evaluate_proof_is_idempotent(client: TestClient) -> None:
    response = client.post(
        "/proofs",
        json={
            "subject": "Applicant",
            "claims": [
                {
                    "claim_type": "income",
                    "subject": "Monthly income",
                    "confidence": "0.90",
                },
                {
                    "claim_type": "income",
                    "subject": "Annual bonus",
                    "confidence": "0.70",
                    "verification_status": "verified",
                },
            ],
        },
    )

    assert response.status_code == 201

    proof_id = response.json()["proof"]["id"]

    first = client.post(f"/proofs/{proof_id}/evaluate")
    second = client.post(f"/proofs/{proof_id}/evaluate")

    assert first.status_code == 200
    assert second.status_code == 200

    first_body = first.json()
    second_body = second.json()

    assert second_body["proof"]["id"] == first_body["proof"]["id"]
    assert second_body["proof"]["status"] == first_body["proof"]["status"]
    assert (
        second_body["proof"]["overall_confidence"]
        == first_body["proof"]["overall_confidence"]
    )
    assert len(second_body["claims"]) == len(first_body["claims"]) == 2
def test_evaluate_proof_respects_configured_ready_confidence(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "PROOF_MINIMUM_READY_CONFIDENCE",
        "0.95",
    )
    monkeypatch.setenv(
        "PROOF_MINIMUM_REVIEW_CONFIDENCE",
        "0.00",
    )
    monkeypatch.setenv(
        "PROOF_MINIMUM_SUPPORTED_CLAIM_RATIO",
        "1.00",
    )

    get_settings.cache_clear()

    try:
        create_response = client.post(
            "/proofs",
            json={
                "subject": "Applicant",
                "claims": [
                    {
                        "claim_type": "income",
                        "subject": "Monthly salary",
                        "confidence": "0.90",
                        "verification_status": "verified",
                    },
                    {
                        "claim_type": "income",
                        "subject": "Annual bonus",
                        "confidence": "0.90",
                        "verification_status": "verified",
                    },
                ],
            },
        )

        assert create_response.status_code == 201

        proof_id = create_response.json()["proof"]["id"]

        evaluate_response = client.post(
            f"/proofs/{proof_id}/evaluate",
        )

        assert evaluate_response.status_code == 200

        body = evaluate_response.json()

        assert body["proof"]["status"] == "needs_review"
        assert body["proof"]["overall_confidence"] == "0.9000"
    finally:
        get_settings.cache_clear()





