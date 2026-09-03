from __future__ import annotations

import json
import sqlite3
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.application.ai_investigation.contracts import (
    InvestigationTool,
    InvestigationToolRequest,
)
from app.application.ai_investigation.engine import AIInvestigationEngine
from app.application.ai_investigation.inspect_contract import InspectContractTool
from app.application.ai_investigation.registry import InvestigationToolRegistry
from app.db.base import Base
from app.db.session import get_db
from app.domain.enums.financial import ClaimType
from app.domain.models.financial import FinancialContract
from app.domain.value_objects.financial import ConfidenceScore
from app.main import app
from benchmarks.harness import benchmark

RESULTS_DIR = Path("benchmarks/results")
WARMUPS = 2
ITERATIONS = 5


def _build_contract() -> FinancialContract:
    return FinancialContract(
        id=uuid4(),
        name="M21 AI Latency Contract",
        version=1,
        minimum_confidence=ConfidenceScore(Decimal("0.80")),
        minimum_supported_claim_ratio=Decimal("0.90"),
        required_claim_types=(ClaimType.INCOME,),
    )


def _benchmark_api(
    client: TestClient,
    method: str,
    path: str,
    *,
    workload_size: int,
    json_body: dict | None = None,
) -> dict:
    """Measure an API endpoint."""

    call_number = 0

    def operation() -> None:
        nonlocal call_number
        call_number += 1

        if method == "GET":
            response = client.get(path)
        elif method == "POST":
            request_body = dict(json_body or {})

            if "version" in request_body:
                request_body["version"] = call_number + 1

            if "name" in request_body:
                request_body["name"] = f"{request_body['name']}-{call_number}"

            response = client.post(path, json=request_body)
        else:
            raise ValueError(f"Unsupported benchmark method: {method}")

        if response.status_code >= 400:
            raise RuntimeError(
                f"Benchmark endpoint returned HTTP {response.status_code}: {response.text}"
            )

    result, _outputs = benchmark(
        name=f"{method} {path}",
        workload_size=workload_size,
        operation=operation,
        warmups=WARMUPS,
        iterations=ITERATIONS,
    )

    return result.as_dict()


def run_api_benchmark() -> dict:
    """Measure representative API latency."""

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            contract_payload = {
                "name": "M21 API Latency Contract",
                "version": 1,
                "minimum_confidence": "0.80",
                "minimum_supported_claim_ratio": "0.90",
                "required_claim_types": ["income"],
            }

            response = client.post("/contracts", json=contract_payload)

            if response.status_code != 201:
                raise RuntimeError(
                    "Failed to create API benchmark contract: "
                    f"HTTP {response.status_code}: {response.text}"
                )

            contract_id = response.json()["id"]

            measurements = {
                "health_get": _benchmark_api(
                    client,
                    "GET",
                    "/health",
                    workload_size=1,
                ),
                "ready_get": _benchmark_api(
                    client,
                    "GET",
                    "/ready",
                    workload_size=1,
                ),
                "contract_get_by_id": _benchmark_api(
                    client,
                    "GET",
                    f"/contracts/{contract_id}",
                    workload_size=1,
                ),
                "contract_create": _benchmark_api(
                    client,
                    "POST",
                    "/contracts",
                    workload_size=1,
                    json_body=contract_payload,
                ),
            }

            return {
                "measurements": measurements,
            }
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def run_db_benchmark() -> dict:
    """Measure local SQLite database operation latency."""

    connection = sqlite3.connect(":memory:")

    try:
        connection.execute(
            """
            CREATE TABLE benchmark_records (
                id INTEGER PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        connection.commit()

        select_result, _select_outputs = benchmark(
            name="SQLite SELECT 1",
            workload_size=1,
            operation=lambda: connection.execute("SELECT 1").fetchone(),
            warmups=WARMUPS,
            iterations=ITERATIONS,
        )

        counter = 0

        def insert_and_flush() -> None:
            nonlocal counter
            counter += 1

            cursor = connection.execute(
                "INSERT INTO benchmark_records (value) VALUES (?)",
                (f"contract-{counter}",),
            )
            connection.commit()

            if cursor.lastrowid is None:
                raise RuntimeError("SQLite insert did not return a row id.")

            connection.execute(
                "SELECT value FROM benchmark_records WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()

        insert_result, _insert_outputs = benchmark(
            name="SQLite contract insert and flush",
            workload_size=1,
            operation=insert_and_flush,
            warmups=WARMUPS,
            iterations=ITERATIONS,
        )

        return {
            "database": "sqlite_in_memory",
            "measurements": {
                "select_1": select_result.as_dict(),
                "contract_insert_and_flush": insert_result.as_dict(),
            },
        }
    finally:
        connection.close()


def run_ai_benchmark() -> dict:
    """Measure deterministic AI investigation latency."""

    contract = _build_contract()

    inspect_tool = InspectContractTool({str(contract.id): contract})

    registry = InvestigationToolRegistry(
        handlers={
            InvestigationTool.INSPECT_CONTRACT: inspect_tool,
        },
        permissions={
            InvestigationTool.INSPECT_CONTRACT,
        },
    )

    engine = AIInvestigationEngine(registry)

    def investigate() -> None:
        request = InvestigationToolRequest(
            investigation_id=uuid4(),
            tool=InvestigationTool.INSPECT_CONTRACT,
            target_id=contract.id,
        )

        result = engine.investigate(request)

        if not result.is_success:
            raise RuntimeError(f"AI benchmark investigation failed: {result.status.value}")

    result, _outputs = benchmark(
        name="AI investigation",
        workload_size=1,
        operation=investigate,
        warmups=WARMUPS,
        iterations=ITERATIONS,
    )

    return {
        "tool": InvestigationTool.INSPECT_CONTRACT.value,
        "measurement": result.as_dict(),
        "cost": {
            "measurable": False,
            "reason": (
                "The current deterministic local AI investigation "
                "implementation exposes no provider, token, or monetary "
                "cost accounting."
            ),
        },
    }


def run_benchmark() -> dict:
    """Run the complete Task 10 benchmark suite."""

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    result = {
        "benchmark": "M21 API DB AI latency",
        "api": run_api_benchmark(),
        "db": run_db_benchmark(),
        "ai": run_ai_benchmark(),
    }

    output_path = RESULTS_DIR / "api_db_ai_latency.json"
    output_path.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    return result


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), indent=2))
