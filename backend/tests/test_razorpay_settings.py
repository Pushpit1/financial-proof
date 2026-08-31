from app.infrastructure.razorpay_settings import RazorpaySettings


def test_razorpay_settings_loads_credentials_from_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_key")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "test_secret")

    settings = RazorpaySettings()

    assert settings.key_id == "rzp_test_key"
    assert settings.key_secret == "test_secret"
    assert settings.timeout_seconds == 10.0


def test_razorpay_settings_supports_custom_timeout(
    monkeypatch,
) -> None:
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_key")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "test_secret")
    monkeypatch.setenv("RAZORPAY_TIMEOUT_SECONDS", "5.5")

    settings = RazorpaySettings()

    assert settings.timeout_seconds == 5.5
