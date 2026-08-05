from datetime import date

import pytest

from minuteflow.exceptions import InputValidationError
from minuteflow.steps.intake import format_numbered_source, intake_notes


def test_intake_preserves_physical_lines_and_normalizes_newlines() -> None:
    document = intake_notes("Alpha\r\n\r\nBeta", meeting_date=date(2026, 8, 5))

    assert [line.number for line in document.lines] == [1, 2, 3]
    assert [line.text for line in document.lines] == ["Alpha", "", "Beta"]
    assert format_numbered_source(document) == "L1: Alpha\nL2: \nL3: Beta"
    assert document.meeting_date == date(2026, 8, 5)


def test_intake_rejects_empty_input() -> None:
    with pytest.raises(InputValidationError, match="empty"):
        intake_notes("  \n ")


def test_intake_rejects_input_over_limit() -> None:
    with pytest.raises(InputValidationError, match="configured limit"):
        intake_notes("12345", max_input_chars=4)
