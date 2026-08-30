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
    assert body["proof"]["evaluation_reasons"] == ["evaluation_passed"]
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
    assert body["proof"]["evaluation_reasons"] == ["no_claims"]
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
    assert body["proof"]["evaluation_reasons"] == ["contradicted_claim"]


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
    assert body["proof"]["evaluation_reasons"] == ["evaluation_passed"]
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
        assert body["proof"]["evaluation_reasons"] == [
            "confidence_below_ready_threshold"
        ]
    finally:
        get_settings.cache_clear()
def test_evaluate_proof_respects_configured_review_confidence(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "PROOF_MINIMUM_READY_CONFIDENCE",
        "0.95",
    )
    monkeypatch.setenv(
        "PROOF_MINIMUM_REVIEW_CONFIDENCE",
        "0.80",
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
                        "confidence": "0.80",
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
        assert body["proof"]["overall_confidence"] == "0.8000"
        assert body["proof"]["evaluation_reasons"] == [
            "confidence_below_ready_threshold"
        ]
        assert body["proof"]["evaluation_reasons"] == [
            "confidence_below_ready_threshold"
        ]
    finally:
        get_settings.cache_clear()


def test_evaluate_proof_respects_configured_supported_claim_ratio(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "PROOF_MINIMUM_READY_CONFIDENCE",
        "0.70",
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
                        "verification_status": "unverified",
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
        assert body["proof"]["evaluation_reasons"] == [
            "unverified_claim",
            "supported_claim_ratio_below_threshold",
        ]
    finally:
        get_settings.cache_clear()













def test_list_proof_evaluations_returns_history(
    client: TestClient,
) -> None:
    response = client.post(
        "/proofs",
        json={
            "subject": "Applicant",
            "claims": [
                {
                    "claim_type": "income",
                    "subject": "Monthly income",
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

    first = client.post(f"/proofs/{proof_id}/evaluate")
    second = client.post(f"/proofs/{proof_id}/evaluate")

    assert first.status_code == 200
    assert second.status_code == 200

    history_response = client.get(
        f"/proofs/{proof_id}/evaluations"
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert len(history) == 2

    assert history[0]["proof_id"] == proof_id
    assert history[1]["proof_id"] == proof_id

    assert history[0]["status"] == "ready"
    assert history[1]["status"] == "ready"

    assert history[0]["overall_confidence"] == "0.8000"
    assert history[1]["overall_confidence"] == "0.8000"

    assert history[0]["evaluation_reasons"] == ["evaluation_passed"]
    assert history[1]["evaluation_reasons"] == ["evaluation_passed"]

    assert history[0]["id"] != history[1]["id"]

    assert history[0]["evaluated_at"]
    assert history[1]["evaluated_at"]


def test_list_proof_evaluations_returns_empty_history(
    client: TestClient,
) -> None:
    response = client.post(
        "/proofs",
        json={"subject": "Applicant"},
    )

    assert response.status_code == 201

    proof_id = response.json()["proof"]["id"]

    history_response = client.get(
        f"/proofs/{proof_id}/evaluations"
    )

    assert history_response.status_code == 200
    assert history_response.json() == []


def test_list_proofs_by_subject_returns_matching_proofs(
    client: TestClient,
) -> None:
    first = client.post(
        "/proofs",
        json={"subject": "Applicant"},
    )
    second = client.post(
        "/proofs",
        json={"subject": "Applicant"},
    )
    other = client.post(
        "/proofs",
        json={"subject": "Other Applicant"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert other.status_code == 201

    first_id = first.json()["proof"]["id"]
    second_id = second.json()["proof"]["id"]
    other_id = other.json()["proof"]["id"]

    response = client.get(
        "/proofs",
        params={"subject": "Applicant"},
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 2
    assert {proof["id"] for proof in body} == {
        first_id,
        second_id,
    }
    assert other_id not in {proof["id"] for proof in body}

    for proof in body:
        assert proof["subject"] == "Applicant"
        assert proof["status"] == "draft"
        assert proof["overall_confidence"] == "0.0000"
        assert proof["evaluation_reasons"] == []


def test_list_proofs_returns_empty_for_unknown_subject(
    client: TestClient,
) -> None:
    response = client.get(
        "/proofs",
        params={"subject": "Unknown Applicant"},
    )

    assert response.status_code == 200
    assert response.json() == []

def _create_api_proof(client, subject: str = "API History Applicant") -> str:
    response = client.post(
        "/proofs",
        json={
            "subject": subject,
            "claims": [
                {
                    "claim_type": "income",
                    "subject": "Monthly salary",
                    "verification_status": "verified",
                    "confidence": "0.90",
                    "confidence_level": "high",
                },
                {
                    "claim_type": "income",
                    "subject": "Annual bonus",
                    "verification_status": "verified",
                    "confidence": "0.70",
                    "confidence_level": "medium",
                },
            ],
            "evidence": [],
            "evidence_links": [],
        },
    )

    assert response.status_code == 201
    return response.json()["proof"]["id"]


def test_get_proof_evaluation_history(client) -> None:
    proof_id = _create_api_proof(client)

    first = client.post(f"/proofs/{proof_id}/evaluate")
    second = client.post(f"/proofs/{proof_id}/evaluate")

    assert first.status_code == 200
    assert second.status_code == 200

    response = client.get(f"/proofs/{proof_id}/evaluations")

    assert response.status_code == 200

    history = response.json()

    assert len(history) == 2

    assert history[0]["proof_id"] == proof_id
    assert history[1]["proof_id"] == proof_id

    assert history[0]["status"] == "ready"
    assert history[1]["status"] == "ready"

    assert history[0]["overall_confidence"] == "0.8000"
    assert history[1]["overall_confidence"] == "0.8000"

    assert history[0]["evaluation_reasons"] == ["evaluation_passed"]
    assert history[1]["evaluation_reasons"] == ["evaluation_passed"]

    assert history[0]["evaluated_at"] <= history[1]["evaluated_at"]


def test_get_proof_evaluation_history_returns_empty_list_before_evaluation(
    client,
) -> None:
    proof_id = _create_api_proof(
        client,
        subject="Unevaluated API History Applicant",
    )

    response = client.get(f"/proofs/{proof_id}/evaluations")

    assert response.status_code == 200
    assert response.json() == []


def test_get_proof_evaluation_history_returns_empty_for_missing_proof(
    client,
) -> None:
    from uuid import uuid4

    missing_proof_id = uuid4()

    response = client.get(
        f"/proofs/{missing_proof_id}/evaluations"
    )

    assert response.status_code == 200
    assert response.json() == []

def test_get_proof_evaluation_history_returns_serialized_records(
    client,
) -> None:
    proof_id = _create_api_proof(
        client,
        subject="API History Applicant",
    )

    evaluation = client.post(
        f"/proofs/{proof_id}/evaluate"
    )

    assert evaluation.status_code == 200

    response = client.get(
        f"/proofs/{proof_id}/evaluations"
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["proof_id"] == proof_id
    assert body[0]["status"] == "ready"
    assert body[0]["overall_confidence"] == "0.8000"
    assert body[0]["evaluation_reasons"] == [
        "evaluation_passed",
    ]
    assert body[0]["evaluated_at"]

def test_get_proof_evaluation_history_preserves_repeated_evaluations(
    client,
) -> None:
    proof_id = _create_api_proof(
        client,
        subject="Repeated API History Applicant",
    )

    first = client.post(
        f"/proofs/{proof_id}/evaluate"
    )
    second = client.post(
        f"/proofs/{proof_id}/evaluate"
    )

    assert first.status_code == 200
    assert second.status_code == 200

    response = client.get(
        f"/proofs/{proof_id}/evaluations"
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 2

    assert body[0]["proof_id"] == proof_id
    assert body[1]["proof_id"] == proof_id

    assert body[0]["status"] == "ready"
    assert body[1]["status"] == "ready"

    assert body[0]["overall_confidence"] == "0.8000"
    assert body[1]["overall_confidence"] == "0.8000"

    assert body[0]["evaluation_reasons"] == [
        "evaluation_passed",
    ]
    assert body[1]["evaluation_reasons"] == [
        "evaluation_passed",
    ]

    assert body[0]["id"] != body[1]["id"]
    assert body[0]["evaluated_at"] <= body[1]["evaluated_at"]
