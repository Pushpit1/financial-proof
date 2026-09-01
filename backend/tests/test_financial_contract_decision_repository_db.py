from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.db.repositories.financial_contract_decision import (
    SqlAlchemyFinancialContractDecisionRepository,
)
from app.domain.models.financial import FinancialContractDecision


def make_decision(
    *,
    passed: bool,
    contract_id=None,
    evaluated_at: datetime | None = None,
) -> FinancialContractDecision:
    return FinancialContractDecision(
        id=uuid4(),
        contract_id=contract_id or uuid4(),
        passed=passed,
        reason_codes=(
            "evaluation_passed",
        )
        if passed
        else (
            "contract_validation_failed",
        ),
        violation_count=1,
        evaluated_at=evaluated_at or datetime.now(UTC),
    )


def test_repository_round_trips_decision(db) -> None:
    repository = SqlAlchemyFinancialContractDecisionRepository(db)

    decision = make_decision(passed=True)

    repository.save(decision)
    db.commit()

    loaded = repository.get_by_id(decision.id)

    assert loaded is not None
    assert loaded.id == decision.id
    assert loaded.contract_id == decision.contract_id
    assert loaded.passed is True
    assert loaded.reason_codes == ("evaluation_passed",)


def test_repository_returns_none_for_unknown_id(db) -> None:
    repository = SqlAlchemyFinancialContractDecisionRepository(db)

    assert repository.get_by_id(uuid4()) is None


def test_repository_lists_decisions_deterministically(db) -> None:
    repository = SqlAlchemyFinancialContractDecisionRepository(db)

    contract_id = uuid4()

    first = make_decision(
        passed=True,
        contract_id=contract_id,
        evaluated_at=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    second = make_decision(
        passed=False,
        contract_id=contract_id,
        evaluated_at=datetime(
            2026,
            1,
            2,
            tzinfo=UTC,
        ),
    )

    repository.save(second)
    repository.save(first)
    db.commit()

    decisions = repository.list_by_contract(contract_id)

    assert [decision.id for decision in decisions] == [
        first.id,
        second.id,
    ]


def test_decision_persistence_commits_through_real_unit_of_work(db) -> None:
    from app.db.unit_of_work import FinancialUnitOfWork
    from app.domain.models.financial import FinancialContract

    contract = FinancialContract(
        name="Real Transaction Commit Contract",
    )

    decision = FinancialContractDecision(
        contract_id=contract.id,
        passed=True,
        reason_codes=(),
        violation_count=0,
    )

    with FinancialUnitOfWork(db) as unit_of_work:
        unit_of_work.decisions.save(decision)

    repository = SqlAlchemyFinancialContractDecisionRepository(db)

    loaded = repository.get_by_id(decision.id)

    assert loaded is not None
    assert loaded.id == decision.id
    assert loaded.contract_id == contract.id
    assert loaded.passed is True


def test_decision_persistence_rolls_back_on_unit_of_work_failure(
    db,
) -> None:
    from app.db.unit_of_work import FinancialUnitOfWork

    decision = make_decision(passed=True)

    with pytest.raises(RuntimeError, match="force rollback"):
        with FinancialUnitOfWork(db) as unit_of_work:
            unit_of_work.decisions.save(decision)

            raise RuntimeError("force rollback")

    repository = SqlAlchemyFinancialContractDecisionRepository(db)

    loaded = repository.get_by_id(decision.id)

    assert loaded is None



