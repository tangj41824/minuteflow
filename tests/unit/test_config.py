import pytest

from minuteflow.config import Settings
from minuteflow.exceptions import ConfigurationError


def _clear_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "MINUTEFLOW_MODEL",
        "MINUTEFLOW_REASONING_EFFORT",
        "MINUTEFLOW_ENABLE_TRACING",
        "MINUTEFLOW_MAX_INPUT_CHARS",
        "MINUTEFLOW_BASE_URL",
        "MINUTEFLOW_API_KEY",
        "DEEPSEEK_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)


def test_settings_use_privacy_safe_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_settings_env(monkeypatch)

    settings = Settings.from_env()

    assert settings.model == "gpt-5.6-luna"
    assert settings.reasoning_effort == "low"
    assert settings.enable_tracing is False
    assert settings.max_input_chars == 100_000
    assert settings.base_url is None
    assert settings.api_key is None


def test_settings_parse_openai_compatible_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("MINUTEFLOW_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("MINUTEFLOW_MODEL", "deepseek-v4-pro")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")

    settings = Settings.from_env()

    assert settings.base_url == "https://api.deepseek.com"
    assert settings.model == "deepseek-v4-pro"
    assert settings.api_key == "sk-test"


def test_settings_api_key_prefers_minuteflow_var(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_settings_env(monkeypatch)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek")
    monkeypatch.setenv("MINUTEFLOW_API_KEY", "sk-override")

    settings = Settings.from_env()

    assert settings.api_key == "sk-override"


def test_settings_reject_invalid_boolean(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINUTEFLOW_ENABLE_TRACING", "sometimes")
    with pytest.raises(ConfigurationError, match="true or false"):
        Settings.from_env()
