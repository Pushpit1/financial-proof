from app.core.config import Settings


def test_development_configuration_defaults_to_safe_debug_value() -> None:
    settings = Settings(_env_file=None, database_url="sqlite:///./test.db")

    assert settings.app_env == "development"
    assert settings.debug is False


def test_production_requires_api_auth_token() -> None:
    try:
        Settings(
            app_env="production",
            debug=False,
            database_url="sqlite:///./test.db",
        )
    except ValueError as exc:
        assert "API_AUTH_TOKEN is required in production." in str(exc)
    else:
        raise AssertionError("Production configuration without API auth must fail.")


def test_production_rejects_debug_mode() -> None:
    try:
        Settings(
            app_env="production",
            debug=True,
            database_url="sqlite:///./test.db",
            api_auth_token="test-token",
        )
    except ValueError as exc:
        assert "DEBUG must be false in production." in str(exc)
    else:
        raise AssertionError("Production debug mode must fail.")


def test_production_configuration_accepts_secure_values() -> None:
    settings = Settings(
        app_env="production",
        debug=False,
        database_url="sqlite:///./test.db",
        api_auth_token="test-token",
    )

    assert settings.app_env == "production"
    assert settings.debug is False
    assert settings.api_auth_token is not None
