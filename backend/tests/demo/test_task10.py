from decimal import Decimal

from app.demo.pipeline import DemoPipeline
from app.domain.enums.financial import ProofStatus
from app.domain.enums.financial_guardian import GuardianDecision


def test_apply_repair_caps_refund_to_original_payment() -> None:
    pipeline = DemoPipeline()
    contract = pipeline.compile_contract()

    repaired = pipeline.apply_repair(contract)

    assert repaired["refund_amount"] == Decimal("50.00")
    assert repaired["original_payment_amount"] == Decimal("50.00")
    assert repaired["repair"] == "refund_capped_to_original_payment"


def test_rerun_after_repair_has_zero_financial_violations() -> None:
    pipeline = DemoPipeline()
    contract = pipeline.compile_contract()

    repaired = pipeline.apply_repair(contract)

    _, verification, evaluation = pipeline.rerun_after_repair(
        contract,
        repaired,
    )

    assert evaluation.passed is True
    assert evaluation.violations == ()
    assert verification.passed is True


def test_rerun_after_repair_is_deterministic() -> None:
    pipeline = DemoPipeline()
    contract = pipeline.compile_contract()

    repaired = pipeline.apply_repair(contract)

    first = pipeline.rerun_after_repair(contract, repaired)
    second = pipeline.rerun_after_repair(contract, repaired)

    assert first[1].passed is True
    assert second[1].passed is True
    assert first[2].violations == second[2].violations


def test_guardian_blocks_unauthorized_refund() -> None:
    pipeline = DemoPipeline()

    result = pipeline.activate_guardian()

    assert result.decision is GuardianDecision.BLOCK
    assert result.rule == "guardian_policy"


def test_guardian_block_is_for_unauthorized_actor() -> None:
    pipeline = DemoPipeline()

    result = pipeline.activate_guardian()

    assert result.decision is GuardianDecision.BLOCK
    assert "not authorized" in result.reason.lower()


def test_financial_proof_is_ready() -> None:
    pipeline = DemoPipeline()

    proof = pipeline.generate_financial_proof()

    assert proof.status is ProofStatus.READY
    assert proof.overall_confidence.value == Decimal("1.0")
    assert len(proof.claim_ids) == 1


def test_financial_proof_is_deterministic_in_semantics() -> None:
    pipeline = DemoPipeline()

    first = pipeline.generate_financial_proof()
    second = pipeline.generate_financial_proof()

    assert first.subject == second.subject
    assert first.status is second.status
    assert first.overall_confidence == second.overall_confidence
    assert len(first.claim_ids) == len(second.claim_ids) == 1
