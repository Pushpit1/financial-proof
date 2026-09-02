from unittest.mock import patch

from app.startup import main


def test_startup_runs_database_migrations() -> None:
    with patch("app.startup.run_database_migrations") as migration:
        main()

    migration.assert_called_once_with()
