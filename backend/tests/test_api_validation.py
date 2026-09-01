from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.financial_contract import FinancialContractCreateRequest
from app.schemas.financial_contract_decision import (
    FinancialContractDecisionEvaluateRequest,
)
from app.schemas.financial_proof import (
    EvidenceCreateRequest,
    FinancialClaimCreateRequest,
    FinancialProofCreateRequest,
)


def test_contract_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        FinancialContractCreateRequest(
            name="payment",
            version=1,
            minimum_confidence=Decimal("0.8"),
            minimum_supported_claim_ratio=Decimal("0.9"),
            required_claim_types=["income"],
            unexpected="attack",
        )


def test_contract_rejects_empty_required_claim_types() -> None:
    with pytest.raises(ValidationError):
        FinancialContractCreateRequest(
            name="payment",
            version=1,
            minimum_confidence=Decimal("0.8"),
            minimum_supported_claim_ratio=Decimal("0.9"),
            required_claim_types=[],
        )


def test_claim_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        FinancialClaimCreateRequest(
            claim_type="income",
            subject="salary",
            unexpected="attack",
        )


def test_claim_rejects_oversized_subject() -> None:
    with pytest.raises(ValidationError):
        FinancialClaimCreateRequest(
            claim_type="income",
            subject="x" * 256,
        )


def test_claim_rejects_confidence_above_one() -> None:
    with pytest.raises(ValidationError):
        FinancialClaimCreateRequest(
            claim_type="income",
            subject="salary",
            confidence=Decimal("1.01"),
        )


def test_evidence_rejects_oversized_source_name() -> None:
    with pytest.raises(ValidationError):
        EvidenceCreateRequest(
            evidence_type="document",
            source_name="x" * 256,
            received_at=date.today(),
        )


def test_evidence_link_rejects_oversized_explanation() -> None:
    from app.schemas.financial_proof import EvidenceLinkCreateRequest

    with pytest.raises(ValidationError):
        EvidenceLinkCreateRequest(
            claim_id=uuid4(),
            evidence_id=uuid4(),
            explanation="x" * 2001,
        )


def test_proof_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        FinancialProofCreateRequest(
            subject="customer-1",
            unexpected="attack",
        )


def test_proof_rejects_oversized_subject() -> None:
    with pytest.raises(ValidationError):
        FinancialProofCreateRequest(
            subject="x" * 256,
        )


def test_decision_context_rejects_more_than_one_hundred_fields() -> None:
    context = {f"key-{index}": index for index in range(101)}

    with pytest.raises(ValidationError):
        FinancialContractDecisionEvaluateRequest(context=context)
