"""Production application startup helpers."""

from __future__ import annotations

import subprocess
import sys


def run_database_migrations() -> None:
    """Apply all pending Alembic migrations."""

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "upgrade",
            "head",
        ],
        check=False,
    )

    if result.returncode != 0:
        raise SystemExit(
            f"Database migration failed with exit code {result.returncode}."
        )


def main() -> None:
    """Run required startup checks before the application server."""

    run_database_migrations()


if __name__ == "__main__":
    main()

