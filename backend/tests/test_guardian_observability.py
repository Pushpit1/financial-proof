import json

from app.core.logging import configure_logging
from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.financial_guardian import GuardianEvaluation
from app.domain.services.financial_guardian_audit import (
    FinancialGuardianAuditService,
)
from app.domain.services.guardian_policy import GuardianPolicy


def make_evaluation(
    decision: GuardianDecision,
    *,
    rule: str = "refund_approval",
    reason: str = "Refund check completed.",
) -> GuardianEvaluation:
    return GuardianEvaluation(
        decision=decision,
        rule=rule,
        reason=reason,
    )


def read_json_events(output: str) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in output.splitlines()
        if line.strip()
    ]


def test_guardian_policy_logs_final_decision(
    capsys,
) -> None:
    configure_logging()

    result = GuardianPolicy.decide(
        [
            make_evaluation(
                GuardianDecision.ALLOW,
                reason="Approval is present.",
            ),
            make_evaluation(
                GuardianDecision.BLOCK,
                rule="unauthorized_refund_prevention",
                reason="Refund actor is unauthorized.",
            ),
        ]
    )

    output = capsys.readouterr().out
    events = read_json_events(output)

    matching = [
        event
        for event in events
        if event.get("event") == "guardian_decision_evaluated"
    ]

    assert matching
    event = matching[-1]

    assert event["decision"] == "block"
    assert event["rule"] == "guardian_policy"
    assert event["reason"] == (
        "Approval is present. Refund actor is unauthorized."
    )
    assert event["evaluation_count"] == 2
    assert result.decision is GuardianDecision.BLOCK


def test_guardian_policy_logs_empty_evaluation_review(
    capsys,
) -> None:
    configure_logging()

    result = GuardianPolicy.decide([])

    output = capsys.readouterr().out
    events = read_json_events(output)

    matching = [
        event
        for event in events
        if event.get("event") == "guardian_decision_evaluated"
    ]

    assert matching
    event = matching[-1]

    assert event["decision"] == "review"
    assert event["rule"] == "guardian_policy"
    assert event["evaluation_count"] == 0
    assert result.decision is GuardianDecision.REVIEW


def test_guardian_audit_creation_is_logged(
    capsys,
) -> None:
    configure_logging()

    record = FinancialGuardianAuditService.record(
        make_evaluation(
            GuardianDecision.BLOCK,
            rule="duplicate_charge",
            reason="Duplicate charge detected.",
        ),
        operation="charge",
        actor_id="operator-004",
    )

    output = capsys.readouterr().out
    events = read_json_events(output)

    matching = [
        event
        for event in events
        if event.get("event") == "guardian_audit_recorded"
    ]

    assert matching
    event = matching[-1]

    assert event["audit_id"] == str(record.id)
    assert event["operation"] == "charge"
    assert event["rule"] == "duplicate_charge"
    assert event["decision"] == "block"
    assert event["reason"] == "Duplicate charge detected."
    assert event["actor_id"] == "operator-004"


def test_guardian_audit_log_omits_missing_actor(
    capsys,
) -> None:
    configure_logging()

    record = FinancialGuardianAuditService.record(
        make_evaluation(GuardianDecision.ALLOW),
        operation="charge",
    )

    output = capsys.readouterr().out
    events = read_json_events(output)

    matching = [
        event
        for event in events
        if event.get("event") == "guardian_audit_recorded"
    ]

    assert matching
    event = matching[-1]

    assert event["audit_id"] == str(record.id)
    assert event["operation"] == "charge"
    assert event["decision"] == "allow"
    assert "actor_id" not in event
