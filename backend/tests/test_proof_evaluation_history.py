from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models.financial import ProofEvaluationModel
from app.db.repositories.financial import ProofEvaluationRepository


def test_evaluation_repository_adds_and_reads_history(db: Session) -> None:
    session = db

    proof_id = uuid4()

    evaluation = ProofEvaluationModel(
        proof_id=proof_id,
        status="ready",
        overall_confidence=Decimal("0.8000"),
        evaluation_reasons=["evaluation_passed"],
        evaluated_at=datetime.now(UTC),
    )

    repository = ProofEvaluationRepository(session)
    repository.add(evaluation)
    session.commit()

    stored = repository.get_by_id(evaluation.id)

    assert stored is not None
    assert stored.proof_id == proof_id
    assert stored.status == "ready"
    assert stored.overall_confidence == Decimal("0.8000")
    assert stored.evaluation_reasons == ["evaluation_passed"]


def test_evaluation_repository_lists_history_in_time_order(
    db: Session,
) -> None:
    session = db

    proof_id = uuid4()

    older = ProofEvaluationModel(
        proof_id=proof_id,
        status="needs_review",
        overall_confidence=Decimal("0.6000"),
        evaluation_reasons=["confidence_below_ready_threshold"],
        evaluated_at=datetime(
            2026,
            8,
            29,
            10,
            0,
            tzinfo=UTC,
        ),
    )

    newer = ProofEvaluationModel(
        proof_id=proof_id,
        status="ready",
        overall_confidence=Decimal("0.8000"),
        evaluation_reasons=["evaluation_passed"],
        evaluated_at=datetime(
            2026,
            8,
            29,
            11,
            0,
            tzinfo=UTC,
        ),
    )

    repository = ProofEvaluationRepository(session)

    repository.add(newer)
    repository.add(older)
    session.commit()

    history = repository.list_by_proof(proof_id)

    assert [item.id for item in history] == [
        older.id,
        newer.id,
    ]


def test_evaluation_history_is_append_only(db: Session) -> None:
    session = db

    proof_id = uuid4()

    first = ProofEvaluationModel(
        proof_id=proof_id,
        status="needs_review",
        overall_confidence=Decimal("0.6000"),
        evaluation_reasons=["confidence_below_ready_threshold"],
        evaluated_at=datetime(
            2026,
            8,
            29,
            10,
            0,
            tzinfo=UTC,
        ),
    )

    second = ProofEvaluationModel(
        proof_id=proof_id,
        status="ready",
        overall_confidence=Decimal("0.8000"),
        evaluation_reasons=["evaluation_passed"],
        evaluated_at=datetime(
            2026,
            8,
            29,
            11,
            0,
            tzinfo=UTC,
        ),
    )

    repository = ProofEvaluationRepository(session)

    repository.add(first)
    repository.add(second)
    session.commit()

    history = repository.list_by_proof(proof_id)

    assert len(history) == 2
    assert history[0].status == "needs_review"
    assert history[1].status == "ready"

