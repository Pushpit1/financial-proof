"""Integration and security tests for extended platform API routes."""

from __future__ import annotations

import json
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

import app.api.dependencies.authentication as authentication
from app.core.config import Settings
from app.main import app


def test_security_headers_and_system_status(client: TestClient) -> None:
    resp = client.get("/system/status")
    assert resp.status_code == 200
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    data = resp.json()
    assert data["database"] == "connected"
    assert "metrics" in data


def test_ready_returns_503_when_db_unreachable() -> None:
    from app.db.session import get_db

    class BrokenSession:
        def execute(self, *_args, **_kwargs):
            raise RuntimeError("db down")

    def override_broken():
        yield BrokenSession()

    app.dependency_overrides[get_db] = override_broken
    try:
        resp = TestClient(app).get("/ready")
        assert resp.status_code == 503
    finally:
        app.dependency_overrides.clear()


def test_list_contracts_and_simulations(client: TestClient) -> None:
    c_resp = client.post(
        "/contracts",
        json={
            "name": f"ListContract-{uuid4().hex[:8]}",
            "version": 1,
            "minimum_confidence": 0.5,
            "minimum_supported_claim_ratio": 1.0,
            "required_claim_types": ["transaction"],
        },
    )
    assert c_resp.status_code == 201
    listed = client.get("/contracts")
    assert listed.status_code == 200
    assert len(listed.json()) >= 1

    sim_resp = client.post(
        "/simulations",
        json={
            "seed": 42,
            "amount_minor": 10000,
            "currency": "INR",
            "events": [
                {"event": "authorize", "occurred_at": "2026-11-27T10:00:00Z"},
                {"event": "capture", "occurred_at": "2026-11-27T10:01:00Z"},
            ],
        },
    )
    assert sim_resp.status_code == 201
    sims = client.get("/simulations")
    assert sims.status_code == 200
    assert len(sims.json()) >= 1


def test_blast_radius_analysis_and_persistence(client: TestClient) -> None:
    resp = client.post(
        "/blast-radius",
        json={
            "payment_amount": "50.00",
            "refund_amount": "75.00",
            "currency": "INR",
            "persist": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["passed"] is False
    assert data["persisted"] is True
    assert Decimal(data["total_direct_loss"]) == Decimal("75.00")

    fetched = client.get(f"/blast-radius/{data['analysis_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["analysis_id"] == data["analysis_id"]


def test_ai_investigation_endpoints(client: TestClient) -> None:
    tools = client.get("/investigations/tools")
    assert tools.status_code == 200
    assert tools.json()["ai_advisory_only"] is True
    assert tools.json()["overrides_deterministic_verification"] is False

    inv = client.post(
        "/investigations",
        json={"violation_summary": "Duplicate authorize and refund exceeds payment"},
    )
    assert inv.status_code == 200
    body = inv.json()
    assert body["ai_advisory_only"] is True
    assert body["overrides_deterministic_verification"] is False
    assert len(body["recommended_actions"]) >= 2


def test_guardian_evaluate_and_audit(client: TestClient) -> None:
    allow = client.post(
        "/guardian/evaluate",
        json={
            "operation": "capture",
            "actor_id": "tester",
            "amount_minor": 5000,
            "payment_amount_minor": 5000,
            "currency": "INR",
        },
    )
    assert allow.status_code == 200
    assert allow.json()["decision"] == "allow"

    block = client.post(
        "/guardian/evaluate",
        json={
            "operation": "refund",
            "actor_id": "tester",
            "amount_minor": 7500,
            "payment_amount_minor": 5000,
            "currency": "INR",
        },
    )
    assert block.status_code == 200
    assert block.json()["decision"] == "block"
    assert block.json()["persisted"] is True

    audit_resp = client.get("/guardian/audit")
    assert audit_resp.status_code == 200
    assert len(audit_resp.json()) >= 2

    unified = client.get("/audit", params={"category": "guardian"})
    assert unified.status_code == 200
    assert len(unified.json()) >= 2


def test_document_upload_security_reconciliation_and_proof_report(
    client: TestClient,
) -> None:
    # Reject invalid extension
    bad_ext = client.post(
        "/documents/upload",
        files={"file": ("malware.exe", b"MZ...", "application/octet-stream")},
    )
    assert bad_ext.status_code == 422

    # Create a proof first
    proof_resp = client.post(
        "/proofs",
        json={
            "subject": "audit-subject-01",
            "claims": [
                {
                    "claim_type": "transaction",
                    "subject": "order-101",
                    "amount": "100.00",
                    "currency": "INR",
                }
            ],
            "evidence": [],
            "evidence_links": [],
        },
    )
    assert proof_resp.status_code == 201
    proof_id = proof_resp.json()["proof"]["id"]

    # Valid CSV upload with path traversal attempt in filename
    csv_bytes = (
        b"reference,amount,currency,status\n"
        b"tx-1,100.00,INR,captured\n"
        b"tx-2,250.50,INR,captured\n"
    )
    up1 = client.post(
        "/documents/upload",
        data={"proof_id": proof_id},
        files={"file": ("../../ledger.csv", csv_bytes, "text/csv")},
    )
    assert up1.status_code == 201
    u1 = up1.json()
    assert ".." not in u1["filename"]
    assert u1["extracted_row_count"] == 2
    assert Decimal(u1["total_amount"]) == Decimal("350.50")
    assert u1["duplicate_checksum_detected"] is False

    # Second upload of same file detects duplicate checksum
    up2 = client.post(
        "/documents/upload",
        files={"file": ("ledger.csv", csv_bytes, "text/csv")},
    )
    assert up2.status_code == 201
    assert up2.json()["duplicate_checksum_detected"] is True

    # Reconciliation
    recon = client.post(
        "/reconciliation/run",
        json={
            "internal_records": [
                {"reference": "tx-1", "amount": "100.00", "currency": "INR", "status": "captured"},
                {"reference": "tx-2", "amount": "250.50", "currency": "INR", "status": "captured"},
            ],
            "provider_records": [
                {"reference": "tx-1", "amount": "100.00", "currency": "INR", "status": "captured"},
                {"reference": "tx-2", "amount": "200.00", "currency": "INR", "status": "captured"},
            ],
        },
    )
    assert recon.status_code == 200
    r_data = recon.json()
    assert r_data["matched_count"] == 1
    assert r_data["discrepancy_count"] == 1
    assert Decimal(r_data["total_exposure"]) == Decimal("50.50")

    # Export reports (json, csv, markdown)
    rep_json = client.get(f"/proofs/{proof_id}/report", params={"format": "json"})
    assert rep_json.status_code == 200
    assert rep_json.json()["proof"]["id"] == proof_id

    rep_csv = client.get(f"/proofs/{proof_id}/report", params={"format": "csv"})
    assert rep_csv.status_code == 200
    assert "audit-subject-01" in rep_csv.text

    rep_md = client.get(f"/proofs/{proof_id}/report", params={"format": "markdown"})
    assert rep_md.status_code == 200
    assert "# Financial Proof Report" in rep_md.text


def test_auth_status_endpoint(client: TestClient) -> None:
    authentication.settings = Settings(
        database_url="sqlite:///./test.db",
        api_auth_token="test-bearer-123",
    )
    authentication.get_authenticator.cache_clear()
    try:
        r1 = client.get("/auth/status")
        assert r1.status_code == 200
        assert r1.json()["authenticated"] is False

        r2 = client.get(
            "/auth/status",
            headers={"Authorization": "Bearer test-bearer-123"},
        )
        assert r2.status_code == 200
        assert r2.json()["authenticated"] is True
    finally:
        authentication.get_authenticator.cache_clear()
        json.dumps({})


def test_ready_returns_503_when_schema_incomplete() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from sqlalchemy.pool import StaticPool

    from app.db.session import get_db

    empty_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    def override_empty_db():
        with Session(empty_engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_empty_db
    try:
        resp = TestClient(app).get("/ready")
        assert resp.status_code == 503
        assert "schema" in resp.json()["detail"].lower()

        status_resp = TestClient(app).get("/system/status")
        assert status_resp.status_code == 200
        payload = status_resp.json()
        assert payload["database"] == "connected"
        assert payload["schema_ready"] is False
        assert "financial_contracts" in payload["missing_tables"]
    finally:
        app.dependency_overrides.clear()
        empty_engine.dispose()


def test_schema_bootstrap_runs_alembic_and_preserves_existing_data(tmp_path) -> None:
    from sqlalchemy import create_engine, text

    from app.db.bootstrap import (
        ALEMBIC_HEAD_REVISION,
        ensure_schema_initialized,
        inspect_schema,
    )

    db_file = tmp_path / "bootstrap_preserve.db"
    eng = create_engine(f"sqlite:///{db_file}")
    try:
        with eng.begin() as conn:
            conn.execute(text("CREATE TABLE custom_user_notes (id INTEGER PRIMARY KEY, note TEXT)"))
            conn.execute(text("INSERT INTO custom_user_notes (id, note) VALUES (1, 'preserve-me')"))

        ensure_schema_initialized(eng)

        with eng.connect() as conn:
            info = inspect_schema(conn)
            assert info["schema_ready"] is True
            assert info["missing_tables"] == []
            assert info["alembic_revision"] == ALEMBIC_HEAD_REVISION
            preserved = conn.execute(
                text("SELECT note FROM custom_user_notes WHERE id = 1")
            ).scalar()
            assert preserved == "preserve-me"
    finally:
        eng.dispose()


def test_create_proof_respects_strict_foreign_keys() -> None:
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import Session
    from sqlalchemy.pool import StaticPool

    from app.db.bootstrap import ensure_schema_initialized
    from app.db.session import get_db

    fk_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(fk_engine, "connect")
    def _enable_sqlite_fks(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    ensure_schema_initialized(fk_engine)

    def override_fk_db():
        with Session(fk_engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_fk_db
    try:
        cid, eid = str(uuid4()), str(uuid4())
        resp = TestClient(app).post(
            "/proofs",
            json={
                "subject": "strict-fk-subject",
                "claims": [
                    {
                        "id": cid,
                        "claim_type": "balance",
                        "subject": "strict-fk-subject",
                        "amount": 100,
                        "currency": "USD",
                        "verification_status": "verified",
                        "confidence": 0.95,
                        "confidence_level": "high",
                    }
                ],
                "evidence": [
                    {
                        "id": eid,
                        "evidence_type": "accounting_record",
                        "source_name": "fk.csv",
                        "received_at": "2026-11-27",
                        "status": "verified",
                    }
                ],
                "evidence_links": [
                    {
                        "claim_id": cid,
                        "evidence_id": eid,
                        "verification_status": "supported",
                        "confidence": 0.95,
                    }
                ],
            },
        )
        assert resp.status_code == 201
    finally:
        app.dependency_overrides.clear()
        fk_engine.dispose()
