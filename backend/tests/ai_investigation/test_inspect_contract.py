from uuid import uuid4

from app.application.ai_investigation.contracts import (
    InvestigationTool,
    InvestigationToolRequest,
    ToolExecutionStatus,
)
from app.application.ai_investigation.inspect_contract import (
    InspectContractTool,
)
from app.domain.models.financial import FinancialContract


def test_inspect_contract_returns_bounded_contract_data() -> None:
    contract = FinancialContract(
        name="Inspection Contract",
        version=3,
    )

    tool = InspectContractTool({str(contract.id): contract})

    request = InvestigationToolRequest(
        tool=InvestigationTool.INSPECT_CONTRACT,
        target_id=contract.id,
    )

    result = tool(request)

    assert result.status is ToolExecutionStatus.SUCCESS
    assert result.data["id"] == str(contract.id)
    assert result.data["name"] == "Inspection Contract"
    assert result.data["version"] == 3
    assert "execution" not in result.data
    assert "state" not in result.data
    assert "financial_impact" not in result.data


def test_inspect_contract_returns_not_found() -> None:
    target_id = uuid4()

    tool = InspectContractTool({})

    request = InvestigationToolRequest(
        tool=InvestigationTool.INSPECT_CONTRACT,
        target_id=target_id,
    )

    result = tool(request)

    assert result.status is ToolExecutionStatus.NOT_FOUND
    assert result.data == {}


def test_inspect_contract_is_deterministic() -> None:
    contract = FinancialContract(
        name="Deterministic Contract",
        version=2,
    )

    tool = InspectContractTool({str(contract.id): contract})

    first = tool(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_CONTRACT,
            target_id=contract.id,
        )
    )
    second = tool(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_CONTRACT,
            target_id=contract.id,
        )
    )

    assert first.data == second.data
    assert first.explanation == second.explanation
