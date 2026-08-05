import pytest

from minuteflow.config import Settings
from minuteflow.exceptions import ConfigurationError


def test_settings_use_privacy_safe_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "MINUTEFLOW_MODEL",
        "MINUTEFLOW_REASONING_EFFORT",
        "MINUTEFLOW_ENABLE_TRACING",
        "MINUTEFLOW_MAX_INPUT_CHARS",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings.from_env()

    assert settings.model == "gpt-5.6-luna"
    assert settings.reasoning_effort == "low"
    assert settings.enable_tracing is False
    assert settings.max_input_chars == 100_000


def test_settings_reject_invalid_boolean(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINUTEFLOW_ENABLE_TRACING", "sometimes")
    with pytest.raises(ConfigurationError, match="true or false"):
        Settings.from_env()
