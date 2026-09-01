from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.financial_guardian import GuardianEvaluation
from app.domain.models.financial_guardian_audit import (
    FinancialGuardianAuditRecord,
)
from app.domain.services.financial_guardian_audit import (
    FinancialGuardianAuditService,
)


def make_evaluation(
    decision: GuardianDecision,
) -> GuardianEvaluation:
    return GuardianEvaluation(
        decision=decision,
        rule="refund_approval",
        reason="Refund approval is missing.",
    )


def test_audit_record_preserves_guardian_decision() -> None:
    evaluation = make_evaluation(GuardianDecision.BLOCK)

    record = FinancialGuardianAuditService.record(
        evaluation,
        operation="refund",
        actor_id="operator-001",
    )

    assert record.decision is GuardianDecision.BLOCK
    assert record.rule == "refund_approval"
    assert record.reason == "Refund approval is missing."
    assert record.operation == "refund"
    assert record.actor_id == "operator-001"


def test_audit_record_has_timestamp() -> None:
    before = datetime.now(UTC)

    record = FinancialGuardianAuditService.record(
        make_evaluation(GuardianDecision.ALLOW),
        operation="charge",
    )

    after = datetime.now(UTC)

    assert before <= record.created_at <= after


def test_audit_record_is_immutable() -> None:
    record = FinancialGuardianAuditService.record(
        make_evaluation(GuardianDecision.BLOCK),
        operation="refund",
    )

    with pytest.raises(ValidationError):
        record.decision = GuardianDecision.ALLOW


def test_audit_record_rejects_empty_operation() -> None:
    with pytest.raises(ValueError, match="Operation cannot be empty"):
        FinancialGuardianAuditService.record(
            make_evaluation(GuardianDecision.ALLOW),
            operation="   ",
        )


def test_audit_record_rejects_empty_actor_id() -> None:
    with pytest.raises(ValueError, match="Actor ID cannot be empty"):
        FinancialGuardianAuditService.record(
            make_evaluation(GuardianDecision.ALLOW),
            operation="refund",
            actor_id="   ",
        )


def test_audit_record_without_actor_is_supported() -> None:
    record = FinancialGuardianAuditService.record(
        make_evaluation(GuardianDecision.REVIEW),
        operation="refund",
    )

    assert record.actor_id is None
    assert record.decision is GuardianDecision.REVIEW


def test_audit_record_has_unique_ids() -> None:
    first = FinancialGuardianAuditRecord(
        operation="refund",
        rule="test",
        decision=GuardianDecision.ALLOW,
        reason="Allowed.",
    )
    second = FinancialGuardianAuditRecord(
        operation="refund",
        rule="test",
        decision=GuardianDecision.ALLOW,
        reason="Allowed.",
    )

    assert first.id != second.id


def test_audit_record_captures_review() -> None:
    record = FinancialGuardianAuditService.record(
        make_evaluation(GuardianDecision.REVIEW),
        operation="refund",
        actor_id="operator-002",
    )

    assert record.decision is GuardianDecision.REVIEW
    assert record.rule == "refund_approval"


def test_audit_record_captures_allow() -> None:
    evaluation = GuardianEvaluation(
        decision=GuardianDecision.ALLOW,
        rule="contract_authorization",
        reason="Operation is authorized.",
    )

    record = FinancialGuardianAuditService.record(
        evaluation,
        operation="refund",
        actor_id="operator-003",
    )

    assert record.decision is GuardianDecision.ALLOW
    assert record.rule == "contract_authorization"


def test_audit_record_captures_block() -> None:
    evaluation = GuardianEvaluation(
        decision=GuardianDecision.BLOCK,
        rule="duplicate_charge",
        reason="Duplicate charge detected.",
    )

    record = FinancialGuardianAuditService.record(
        evaluation,
        operation="charge",
        actor_id="operator-004",
    )

    assert record.decision is GuardianDecision.BLOCK
    assert record.reason == "Duplicate charge detected."
