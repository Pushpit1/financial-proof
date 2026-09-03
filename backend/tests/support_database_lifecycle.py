from __future__ import annotations

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

_sessions: list[Session] = []
_engines: list[Engine] = []


def register_engine(engine: Engine) -> Engine:
    if engine not in _engines:
        _engines.append(engine)
    return engine


def register_session(session: Session, engine: Engine) -> Session:
    _sessions.append(session)
    register_engine(engine)
    return session


def cleanup() -> None:
    while _sessions:
        _sessions.pop().close()

    while _engines:
        _engines.pop().dispose()
