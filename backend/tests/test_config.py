from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_have_expected_application_defaults(monkeypatch) -> None:
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("APP_VERSION", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://financial_proof:test-password@localhost:5433/financial_proof",
    )

    settings = Settings(_env_file=None)

    assert settings.app_name == "Financial Proof API"
    assert settings.app_version == "0.1.0"
    assert settings.debug is False


def test_settings_require_database_url(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://financial_proof:test-password@localhost:5433/financial_proof",
    )

    settings = Settings()

    assert (
        settings.database_url.get_secret_value()
        == "postgresql+psycopg://financial_proof:test-password@localhost:5433/financial_proof"
    )


def test_database_url_is_masked() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://financial_proof:test-password@localhost:5433/financial_proof",
    )

    assert "test-password" not in repr(settings.database_url)


def test_settings_have_default_proof_evaluation_policy() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://financial_proof:test-password@localhost:5433/financial_proof",
    )

    assert settings.proof_minimum_review_confidence == Decimal("0.00")
    assert settings.proof_minimum_ready_confidence == Decimal("0.70")
    assert settings.proof_minimum_supported_claim_ratio == Decimal("1.00")


def test_settings_accept_custom_proof_evaluation_policy() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://financial_proof:test-password@localhost:5433/financial_proof",
        proof_minimum_review_confidence=Decimal("0.10"),
        proof_minimum_ready_confidence=Decimal("0.80"),
        proof_minimum_supported_claim_ratio=Decimal("0.75"),
    )

    assert settings.proof_minimum_review_confidence == Decimal("0.10")
    assert settings.proof_minimum_ready_confidence == Decimal("0.80")
    assert settings.proof_minimum_supported_claim_ratio == Decimal("0.75")


def test_settings_parse_environment_values(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://financial_proof:test-password@localhost:5433/financial_proof",
    )
    monkeypatch.setenv("PROOF_MINIMUM_REVIEW_CONFIDENCE", "0.20")
    monkeypatch.setenv("PROOF_MINIMUM_READY_CONFIDENCE", "0.85")
    monkeypatch.setenv("PROOF_MINIMUM_SUPPORTED_CLAIM_RATIO", "0.90")

    settings = Settings()

    assert settings.proof_minimum_review_confidence == Decimal("0.20")
    assert settings.proof_minimum_ready_confidence == Decimal("0.85")
    assert settings.proof_minimum_supported_claim_ratio == Decimal("0.90")


def test_settings_reject_review_confidence_above_one() -> None:
    with pytest.raises(
        ValidationError,
        match="Proof minimum review confidence must be between 0 and 1",
    ):
        Settings(
            database_url="postgresql+psycopg://financial_proof:test-password@localhost:5433/financial_proof",
            proof_minimum_review_confidence=Decimal("1.01"),
        )


def test_settings_reject_ready_confidence_above_one() -> None:
    with pytest.raises(
        ValidationError,
        match="Proof minimum ready confidence must be between 0 and 1",
    ):
        Settings(
            database_url="postgresql+psycopg://financial_proof:test-password@localhost:5433/financial_proof",
            proof_minimum_ready_confidence=Decimal("1.01"),
        )


def test_settings_reject_supported_claim_ratio_above_one() -> None:
    with pytest.raises(
        ValidationError,
        match="Proof minimum supported claim ratio must be between 0 and 1",
    ):
        Settings(
            database_url="postgresql+psycopg://financial_proof:test-password@localhost:5433/financial-proof",
            proof_minimum_supported_claim_ratio=Decimal("1.01"),
        )


def test_settings_reject_review_confidence_above_ready_confidence() -> None:
    with pytest.raises(
        ValidationError,
        match="cannot exceed",
    ):
        Settings(
            database_url="postgresql+psycopg://financial_proof:test-password@localhost:5433/financial-proof",
            proof_minimum_review_confidence=Decimal("0.80"),
            proof_minimum_ready_confidence=Decimal("0.70"),
        )


def test_settings_accept_zero_and_one_boundaries() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://financial_proof:test-password@localhost:5433/financial-proof",
        proof_minimum_review_confidence=Decimal("0"),
        proof_minimum_ready_confidence=Decimal("1"),
        proof_minimum_supported_claim_ratio=Decimal("1"),
    )

    assert settings.proof_minimum_review_confidence == Decimal("0")
    assert settings.proof_minimum_ready_confidence == Decimal("1")
    assert settings.proof_minimum_supported_claim_ratio == Decimal("1")


def test_settings_reject_environment_review_above_ready(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://financial_proof:test-password@localhost:5433/financial-proof",
    )
    monkeypatch.setenv("PROOF_MINIMUM_REVIEW_CONFIDENCE", "0.80")
    monkeypatch.setenv("PROOF_MINIMUM_READY_CONFIDENCE", "0.70")

    with pytest.raises(
        ValidationError,
        match="Proof minimum review confidence cannot exceed "
        "proof minimum ready confidence",
    ):
        Settings()


def test_settings_reject_environment_ready_above_one(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://financial_proof:test-password@localhost:5433/financial-proof",
    )
    monkeypatch.setenv("PROOF_MINIMUM_READY_CONFIDENCE", "1.01")

    with pytest.raises(
        ValidationError,
        match="Proof minimum ready confidence must be between 0 and 1",
    ):
        Settings()


def test_settings_reject_environment_supported_claim_ratio_above_one(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://financial_proof:test-password@localhost:5433/financial-proof",
    )
    monkeypatch.setenv("PROOF_MINIMUM_SUPPORTED_CLAIM_RATIO", "1.01")

    with pytest.raises(
        ValidationError,
        match="Proof minimum supported claim ratio must be between 0 and 1",
    ):
        Settings()


def test_settings_reject_environment_negative_review_confidence(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://financial_proof:test-password@localhost:5433/financial-proof",
    )
    monkeypatch.setenv("PROOF_MINIMUM_REVIEW_CONFIDENCE", "-0.01")

    with pytest.raises(
        ValidationError,
        match="Proof minimum review confidence must be between 0 and 1",
    ):
        Settings()


def test_settings_reject_environment_negative_ready_confidence(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://financial_proof:test-password@localhost:5433/financial-proof",
    )
    monkeypatch.setenv("PROOF_MINIMUM_READY_CONFIDENCE", "-0.01")

    with pytest.raises(
        ValidationError,
        match="Proof minimum ready confidence must be between 0 and 1",
    ):
        Settings()


def test_settings_reject_environment_negative_supported_claim_ratio(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://financial_proof:test-password@localhost:5433/financial-proof",
    )
    monkeypatch.setenv("PROOF_MINIMUM_SUPPORTED_CLAIM_RATIO", "-0.01")

    with pytest.raises(
        ValidationError,
        match="Proof minimum supported claim ratio must be between 0 and 1",
    ):
        Settings()
