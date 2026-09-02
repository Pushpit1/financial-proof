"""Tests for deterministic demo AI investigation."""

from app.application.ai_investigation.contracts import ToolExecutionStatus
from app.demo.pipeline import DemoPipeline
from app.demo.seed import build_demo_seed


def test_demo_pipeline_ai_investigation_succeeds() -> None:
    seed = build_demo_seed()
    pipeline = DemoPipeline(seed)
    contract = pipeline.compile_contract()

    investigation = pipeline.investigate(contract)

    assert investigation["status"] == ToolExecutionStatus.SUCCESS.value
    assert investigation["investigation_id"]
    assert investigation["tools"] == (
        "inspect_contract",
        "inspect_execution",
    )


def test_demo_pipeline_ai_investigation_is_deterministic() -> None:
    seed = build_demo_seed()
    contract = DemoPipeline(seed).compile_contract()

    first = DemoPipeline(seed).investigate(contract)
    second = DemoPipeline(seed).investigate(contract)

    assert first == second


def test_demo_pipeline_ai_investigation_inspects_contract() -> None:
    seed = build_demo_seed()
    pipeline = DemoPipeline(seed)
    contract = pipeline.compile_contract()

    investigation = pipeline.investigate(contract)

    assert investigation["contract"]["id"] == str(seed.contract_id)
    assert investigation["contract"]["name"] == seed.contract_name
    assert investigation["contract"]["version"] == seed.contract_version


def test_demo_pipeline_ai_investigation_inspects_attack_execution() -> None:
    seed = build_demo_seed()
    pipeline = DemoPipeline(seed)
    contract = pipeline.compile_contract()

    investigation = pipeline.investigate(contract)

    events = investigation["execution"]["events"]

    assert len(events) == 3
    assert tuple(event["event"] for event in events) == (
        "authorize",
        "authorize",
        "capture",
    )


def test_demo_pipeline_ai_investigation_derives_root_cause() -> None:
    seed = build_demo_seed()
    pipeline = DemoPipeline(seed)
    contract = pipeline.compile_contract()

    investigation = pipeline.investigate(contract)

    assert investigation["root_cause"] == (
        "Contract 'customer-refund-safety' was exposed to a duplicate "
        "'authorize' event before the normal payment progression completed."
    )


def test_demo_pipeline_ai_investigation_does_not_fabricate_claims() -> None:
    seed = build_demo_seed()
    pipeline = DemoPipeline(seed)
    contract = pipeline.compile_contract()

    investigation = pipeline.investigate(contract)

    assert "recommendation" not in investigation
    assert "financial_impact" not in investigation["contract"]
    assert "root_cause" not in investigation["contract"]
    assert "root_cause" not in investigation["execution"]
