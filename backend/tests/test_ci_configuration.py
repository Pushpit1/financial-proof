from pathlib import Path


def test_ci_workflow_exists() -> None:
    path = Path(".github/workflows/ci.yml")

    assert path.is_file()


def test_ci_workflow_contains_backend_quality_gates() -> None:
    text = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "python -m ruff check ." in text
    assert "python -m compileall -q app tests" in text
    assert "python -m pytest" in text
    assert "--cov=app" in text
    assert "--cov-fail-under=80" in text


def test_ci_workflow_contains_frontend_quality_gates() -> None:
    text = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "npm ci" in text
    assert "npm run lint" in text
    assert "npm run build" in text


def test_ci_workflow_targets_main_branch() -> None:
    text = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "branches:" in text
    assert "- main" in text


def test_ci_workflow_uses_read_only_repository_permissions() -> None:
    text = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "permissions:" in text
    assert "contents: read" in text
