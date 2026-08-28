from fastapi.testclient import TestClient


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

def test_get_proof_returns_complete_aggregate(client: TestClient) -> None:
    from datetime import date

    from app.application.services.financial_proof import (
        FinancialProofApplicationService,
    )
    from app.db.session import get_db
    from app.db.unit_of_work import FinancialUnitOfWork
    from app.domain.enums.financial import EvidenceType
    from app.domain.models.financial import Evidence, FinancialProof

    db = next(get_db())
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

