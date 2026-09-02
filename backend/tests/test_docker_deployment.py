from pathlib import Path

DOCKERFILE = Path("Dockerfile")


def _dockerfile() -> str:
    return DOCKERFILE.read_text(encoding="utf-8")


def test_dockerfile_uses_python_314() -> None:
    content = _dockerfile()

    assert "FROM python:3.14-slim" in content


def test_dockerfile_runs_as_non_root_user() -> None:
    content = _dockerfile()

    assert "useradd --create-home --uid 10001" in content
    assert "USER appuser" in content


def test_dockerfile_has_healthcheck() -> None:
    content = _dockerfile()

    assert "HEALTHCHECK" in content
    assert "/health" in content


def test_dockerfile_runs_migrations_before_server() -> None:
    content = _dockerfile()

    assert "python -m app.startup" in content
    assert "exec uvicorn app.main:app" in content
    assert content.index("python -m app.startup") < content.index(
        "exec uvicorn app.main:app"
    )


def test_dockerfile_exposes_api_port() -> None:
    content = _dockerfile()

    assert "EXPOSE 8000" in content


def test_dockerfile_disables_pip_cache() -> None:
    content = _dockerfile()

    assert "PIP_NO_CACHE_DIR=1" in content


def test_dockerfile_preserves_unbuffered_logging() -> None:
    content = _dockerfile()

    assert "PYTHONUNBUFFERED=1" in content
