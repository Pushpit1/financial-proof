"""Non-destructive database schema inspection and idempotent bootstrap helpers."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from alembic.config import Config
from sqlalchemy import Connection, Engine, inspect, text

import app.db.models.financial  # noqa: F401
import app.db.models.financial_guardian_audit  # noqa: F401
from alembic import command
from app.db.base import Base

logger = logging.getLogger(__name__)

REQUIRED_TABLES: tuple[str, ...] = (
    "evidence",
    "financial_claims",
    "evidence_links",
    "financial_contracts",
    "financial_proofs",
    "proof_evaluations",
    "financial_contract_decisions",
    "financial_blast_radius",
    "financial_exposures",
    "financial_guardian_audit_records",
)

ALEMBIC_HEAD_REVISION = "b1c2d3e4f5a6"
_PG_BOOTSTRAP_LOCK_KEY = 88412091

_bootstrap_lock = threading.Lock()
_bootstrapped_engine_keys: set[tuple[int, str]] = set()


def _alembic_config() -> Config:
    backend_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    cfg.attributes["skip_logging_config"] = True
    return cfg


def inspect_schema(connection: Connection) -> dict[str, object]:
    """Inspect required tables and Alembic revision on an active DB connection."""
    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())
    missing_tables = [t for t in REQUIRED_TABLES if t not in existing_tables]

    alembic_revision: str | None = None
    if "alembic_version" in existing_tables:
        row = connection.execute(
            text("SELECT version_num FROM alembic_version LIMIT 1")
        ).fetchone()
        if row is not None:
            alembic_revision = str(row[0])

    return {
        "tables": sorted(existing_tables),
        "missing_tables": missing_tables,
        "alembic_revision": alembic_revision,
        "schema_ready": len(missing_tables) == 0,
    }


def ensure_schema_initialized(engine: Engine) -> None:
    """Safely initialize missing schema via Alembic without altering existing data."""
    engine_key = (id(engine), str(engine.url))
    if engine_key in _bootstrapped_engine_keys:
        return

    with _bootstrap_lock:
        if engine_key in _bootstrapped_engine_keys:
            return

        try:
            with engine.begin() as conn:
                if conn.dialect.name == "postgresql":
                    conn.execute(
                        text("SELECT pg_advisory_xact_lock(:lock_key)"),
                        {"lock_key": _PG_BOOTSTRAP_LOCK_KEY},
                    )

                status = inspect_schema(conn)
                existing_tables = set(status["tables"])  # type: ignore[arg-type]
                missing_tables: list[str] = status["missing_tables"]  # type: ignore[assignment]

                if missing_tables:
                    any_required_present = any(
                        t in existing_tables for t in REQUIRED_TABLES
                    )
                    if "alembic_version" in existing_tables or not any_required_present:
                        cfg = _alembic_config()
                        cfg.attributes["connection"] = conn
                        command.upgrade(cfg, "head")
                    else:
                        # Add missing tables non-destructively when legacy tables already exist.
                        Base.metadata.create_all(bind=conn, checkfirst=True)
                        cfg = _alembic_config()
                        cfg.attributes["connection"] = conn
                        command.stamp(cfg, ALEMBIC_HEAD_REVISION)

                    status = inspect_schema(conn)

                if status["schema_ready"]:
                    _bootstrapped_engine_keys.add(engine_key)
        except Exception as exc:
            # Leave DB errors for readiness checks and route handlers to surface cleanly.
            logger.warning("Database schema bootstrap skipped: %s", type(exc).__name__)
