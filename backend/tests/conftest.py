from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from tests.support_database_lifecycle import cleanup, register_engine, register_session


def create_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return register_session(Session(engine), engine)


@pytest.fixture(autouse=True)
def cleanup_sqlalchemy_resources() -> Generator[None, None, None]:
    yield
    cleanup()


@pytest.fixture
def db(
    cleanup_sqlalchemy_resources: None,
) -> Generator[Session, None, None]:
    engine = register_engine(
        create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
