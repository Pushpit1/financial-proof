from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


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
    from datetime import date

    from app.application.services.financial_proof import (
        FinancialProofApplicationService,
    )
    from app.db.unit_of_work import FinancialUnitOfWork
    from app.domain.enums.financial import EvidenceType
    from app.domain.models.financial import Evidence, FinancialProof

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


