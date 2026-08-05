"""Checks that run before any model request."""

from minuteflow.exceptions import InputValidationError


def validate_raw_input(text: str, *, max_input_chars: int) -> None:
    if not text or not text.strip():
        raise InputValidationError("The meeting notes are empty.")
    if len(text) > max_input_chars:
        raise InputValidationError(
            f"The meeting notes contain {len(text)} characters; the configured limit is "
            f"{max_input_chars}."
        )
