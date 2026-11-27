import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

_db_url = settings.database_url.get_secret_value()
_engine_kwargs: dict[str, object] = {"pool_pre_ping": True}

if os.environ.get("VERCEL"):
    _engine_kwargs["poolclass"] = NullPool

if _db_url.startswith("postgresql"):
    _engine_kwargs["connect_args"] = {"connect_timeout": 5}

engine = create_engine(_db_url, **_engine_kwargs)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
