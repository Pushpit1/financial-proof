from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.config import Settings


def test_database_url_is_secret_str():
    settings = Settings(
        _env_file=None,
        database_url="sqlite:///./test.db",
    )

    assert settings.database_url.get_secret_value() == "sqlite:///./test.db"
    assert str(settings.database_url) == "**********"


def test_alembic_env_reads_secret_database_url_safely():
    text = Path("alembic/env.py").read_text(encoding="utf-8")

    assert "settings.database_url.get_secret_value()" in text
    assert "settings.database_url.replace(" not in text


def test_alembic_configuration_has_expected_script_location():
    config = Config("alembic.ini")

    script_location = Path(
        config.get_main_option("script_location")
    ).resolve()

    assert script_location == Path("alembic").resolve()


def test_alembic_has_single_head():
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)

    heads = script.get_heads()

    assert heads == ["b1c2d3e4f5a6"]


def test_alembic_has_linear_history_to_base():
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)

    revisions = list(script.walk_revisions())

    assert revisions
    assert revisions[-1].down_revision is None

    for revision in revisions:
        if revision.down_revision is not None:
            assert script.get_revision(revision.down_revision) is not None
