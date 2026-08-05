"""Source normalization and stable line numbering."""

from __future__ import annotations

from datetime import date

from minuteflow.guardrails.input import validate_raw_input
from minuteflow.schemas import SourceDocument, SourceLine


def intake_notes(
    text: str,
    *,
    meeting_date: date | None = None,
    max_input_chars: int = 100_000,
) -> SourceDocument:
    validate_raw_input(text, max_input_chars=max_input_chars)
    normalized = text.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    lines = [
        SourceLine(number=index, text=line) for index, line in enumerate(normalized.split("\n"), 1)
    ]
    return SourceDocument(lines=lines, meeting_date=meeting_date)


def format_numbered_source(document: SourceDocument) -> str:
    return "\n".join(f"L{line.number}: {line.text}" for line in document.lines)
