from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.db.unit_of_work import FinancialUnitOfWork
from tests.support_database_lifecycle import register_engine


@pytest.fixture
def sqlite_session():
    engine = register_engine(create_engine("sqlite:///:memory:"))
    with engine.connect() as connection:
        connection.execute(
            text(
                "CREATE TABLE transaction_probe "
                "(id INTEGER PRIMARY KEY, value TEXT NOT NULL)"
            )
        )
        connection.commit()

        with Session(bind=connection) as session:
            yield session


def test_unit_of_work_commits_successful_transaction(sqlite_session) -> None:
    with FinancialUnitOfWork(sqlite_session) as unit_of_work:
        sqlite_session.execute(
            text("INSERT INTO transaction_probe (id, value) VALUES (1, 'ok')")
        )
        unit_of_work.flush()

    row = sqlite_session.execute(
        text("SELECT value FROM transaction_probe WHERE id = 1")
    ).scalar_one()

    assert row == "ok"


def test_unit_of_work_rolls_back_application_failure(sqlite_session) -> None:
    with pytest.raises(RuntimeError, match="application failure"):
        with FinancialUnitOfWork(sqlite_session):
            sqlite_session.execute(
                text(
                    "INSERT INTO transaction_probe (id, value) "
                    "VALUES (1, 'should rollback')"
                )
            )
            raise RuntimeError("application failure")

    rows = sqlite_session.execute(
        text("SELECT id FROM transaction_probe")
    ).all()

    assert rows == []


def test_unit_of_work_rolls_back_commit_failure() -> None:
    session = Mock(spec=Session)
    unit_of_work = FinancialUnitOfWork(session)

    session.commit.side_effect = RuntimeError("commit failure")

    with pytest.raises(RuntimeError, match="commit failure"):
        with unit_of_work:
            pass

    session.commit.assert_called_once_with()
    session.rollback.assert_called_once_with()


def test_flush_does_not_commit() -> None:
    session = Mock(spec=Session)
    unit_of_work = FinancialUnitOfWork(session)

    unit_of_work.flush()

    session.flush.assert_called_once_with()
    session.commit.assert_not_called()


def test_successful_unit_of_work_commits_once() -> None:
    session = Mock(spec=Session)

    with FinancialUnitOfWork(session):
        pass

    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()


def test_failed_unit_of_work_rolls_back_once() -> None:
    session = Mock(spec=Session)

    with pytest.raises(ValueError, match="transaction failure"):
        with FinancialUnitOfWork(session):
            raise ValueError("transaction failure")

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()




