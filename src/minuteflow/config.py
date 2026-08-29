"""Environment-backed runtime settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, cast

from minuteflow.exceptions import ConfigurationError

ReasoningEffort = Literal["none", "low", "medium", "high", "xhigh", "max"]
DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_REASONING_EFFORT: ReasoningEffort = "low"
DEFAULT_MAX_INPUT_CHARS = 100_000


def _parse_bool(value: str, *, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(f"{name} must be true or false, got {value!r}.")


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime configuration with privacy-safe defaults."""

    model: str = DEFAULT_MODEL
    reasoning_effort: ReasoningEffort = DEFAULT_REASONING_EFFORT
    enable_tracing: bool = False
    max_input_chars: int = DEFAULT_MAX_INPUT_CHARS
    base_url: str | None = None
    api_key: str | None = None

    @classmethod
    def from_env(
        cls,
        *,
        model_override: str | None = None,
        enable_tracing_override: bool | None = None,
    ) -> Settings:
        model = model_override or os.getenv("MINUTEFLOW_MODEL", DEFAULT_MODEL)
        raw_effort = os.getenv("MINUTEFLOW_REASONING_EFFORT", DEFAULT_REASONING_EFFORT)
        allowed_efforts = {"none", "low", "medium", "high", "xhigh", "max"}
        if raw_effort not in allowed_efforts:
            raise ConfigurationError(
                "MINUTEFLOW_REASONING_EFFORT must be one of: " + ", ".join(sorted(allowed_efforts))
            )

        if enable_tracing_override is None:
            enable_tracing = _parse_bool(
                os.getenv("MINUTEFLOW_ENABLE_TRACING", "false"),
                name="MINUTEFLOW_ENABLE_TRACING",
            )
        else:
            enable_tracing = enable_tracing_override

        raw_limit = os.getenv("MINUTEFLOW_MAX_INPUT_CHARS", str(DEFAULT_MAX_INPUT_CHARS))
        try:
            max_input_chars = int(raw_limit)
        except ValueError as exc:
            raise ConfigurationError("MINUTEFLOW_MAX_INPUT_CHARS must be an integer.") from exc
        if max_input_chars < 1:
            raise ConfigurationError("MINUTEFLOW_MAX_INPUT_CHARS must be greater than zero.")
        if not model.strip():
            raise ConfigurationError("The configured model ID cannot be empty.")

        base_url = os.getenv("MINUTEFLOW_BASE_URL", "").strip() or None
        api_key = os.getenv("MINUTEFLOW_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or None

        return cls(
            model=model.strip(),
            reasoning_effort=cast(ReasoningEffort, raw_effort),
            enable_tracing=enable_tracing,
            max_input_chars=max_input_chars,
            base_url=base_url,
            api_key=api_key,
        )
