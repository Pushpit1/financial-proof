"""Tests for the Financial Guardian runtime orchestrator."""

from app.application.financial_guardian import FinancialGuardianRuntime
from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.financial_guardian import GuardianEvaluation
from app.domain.models.financial_guardian_audit import (
    FinancialGuardianAuditRecord,
)


class InMemoryAuditRepository:
    """Minimal repository used to verify runtime audit persistence."""

    def __init__(self) -> None:
        self.records: list[FinancialGuardianAuditRecord] = []

    def save(
        self,
        record: FinancialGuardianAuditRecord,
    ) -> FinancialGuardianAuditRecord:
        self.records.append(record)
        return record


def make_evaluation(
    decision: GuardianDecision,
    rule: str,
    reason: str,
) -> GuardianEvaluation:
    return GuardianEvaluation(
        decision=decision,
        rule=rule,
        reason=reason,
    )


def test_runtime_blocks_when_any_guard_blocks() -> None:
    runtime = FinancialGuardianRuntime()

    result = runtime.decide(
        [
            make_evaluation(
                GuardianDecision.ALLOW,
                "allow_rule",
                "Operation is valid.",
            ),
            make_evaluation(
                GuardianDecision.BLOCK,
                "blocking_rule",
                "Operation violates a financial rule.",
            ),
        ],
    )

    assert result.decision is GuardianDecision.BLOCK
    assert result.rule == "guardian_policy"


def test_runtime_reviews_when_no_guard_blocks() -> None:
    runtime = FinancialGuardianRuntime()

    result = runtime.decide(
        [
            make_evaluation(
                GuardianDecision.ALLOW,
                "allow_rule",
                "Operation is valid.",
            ),
            make_evaluation(
                GuardianDecision.REVIEW,
                "review_rule",
                "Operation requires review.",
            ),
        ],
    )

    assert result.decision is GuardianDecision.REVIEW


def test_runtime_allows_when_all_guards_allow() -> None:
    runtime = FinancialGuardianRuntime()

    result = runtime.decide(
        [
            make_evaluation(
                GuardianDecision.ALLOW,
                "first_rule",
                "First check passed.",
            ),
            make_evaluation(
                GuardianDecision.ALLOW,
                "second_rule",
                "Second check passed.",
            ),
        ],
    )

    assert result.decision is GuardianDecision.ALLOW


def test_runtime_reviews_when_no_evaluations_exist() -> None:
    runtime = FinancialGuardianRuntime()

    result = runtime.decide([])

    assert result.decision is GuardianDecision.REVIEW


def test_runtime_persists_final_decision_to_audit_repository() -> None:
    repository = InMemoryAuditRepository()
    runtime = FinancialGuardianRuntime(repository)

    result = runtime.decide(
        [
            make_evaluation(
                GuardianDecision.ALLOW,
                "refund_approval",
                "Approval is present.",
            ),
            make_evaluation(
                GuardianDecision.BLOCK,
                "unauthorized_refund_prevention",
                "Refund actor is unauthorized.",
            ),
        ],
        operation="refund",
        actor_id="actor-123",
    )

    assert result.decision is GuardianDecision.BLOCK
    assert len(repository.records) == 1

    record = repository.records[0]

    assert record.operation == "refund"
    assert record.actor_id == "actor-123"
    assert record.decision is GuardianDecision.BLOCK
    assert record.rule == "guardian_policy"
    assert "unauthorized" in record.reason.lower()


def test_runtime_requires_operation_when_audit_is_enabled() -> None:
    repository = InMemoryAuditRepository()
    runtime = FinancialGuardianRuntime(repository)

    evaluations = [
        make_evaluation(
            GuardianDecision.ALLOW,
            "refund_approval",
            "Approval is present.",
        ),
    ]

    try:
        runtime.decide(evaluations)
    except ValueError as exc:
        assert "operation" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError.")
