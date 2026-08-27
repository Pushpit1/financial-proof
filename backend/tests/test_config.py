from app.core.config import settings


def test_settings_loaded():
    assert settings.app_name == "Financial Proof"
    assert settings.app_version == "0.1.0"