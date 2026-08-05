from minuteflow.renderers import render_json, render_markdown
from minuteflow.schemas import MeetingActionReport


def test_renderers_keep_empty_sections_explicit() -> None:
    report = MeetingActionReport(
        summary="No confirmed outcomes.",
        warnings=["No confirmed decisions or explicit action items were found."],
        source_line_count=2,
    )

    markdown = render_markdown(report)
    json_output = render_json(report)

    assert "## Decisions\n\n- None." in markdown
    assert "## Actions\n\n- None." in markdown
    assert '"decisions": []' in json_output
