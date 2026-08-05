"""Stable JSON and Markdown rendering."""

from __future__ import annotations

from minuteflow.schemas import EvidenceReference, MeetingActionReport


def render_json(report: MeetingActionReport) -> str:
    return report.model_dump_json(indent=2)


def _render_evidence(evidence: list[EvidenceReference]) -> list[str]:
    lines: list[str] = []
    for reference in evidence:
        quote = reference.text.replace("\n", " / ")
        lines.append(f"  - Evidence {reference.line_range}: {quote}")
    return lines


def render_markdown(report: MeetingActionReport) -> str:
    meeting_date = report.meeting_date.isoformat() if report.meeting_date else "not provided"
    lines = ["# Meeting Action Report", "", "## Summary", "", report.summary]

    if report.errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in report.errors)

    lines.extend(["", "## Decisions", ""])
    if report.decisions:
        for decision in report.decisions:
            lines.append(f"- **{decision.id}** {decision.statement}")
            lines.extend(_render_evidence(decision.evidence))
    else:
        lines.append("- None.")

    lines.extend(["", "## Actions", ""])
    if report.actions:
        for action in report.actions:
            owner = action.owner or "not specified"
            due_date = action.due_date or "not specified"
            lines.append(
                f"- **{action.id}** {action.task} "
                f"(owner: {owner}; due: {due_date}; status: {action.status})"
            )
            lines.extend(_render_evidence(action.evidence))
    else:
        lines.append("- None.")

    lines.extend(["", "## Clarification Questions", ""])
    lines.extend(
        (f"- {question}" for question in report.clarification_questions),
    )
    if not report.clarification_questions:
        lines.append("- None.")

    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in report.warnings)
    if not report.warnings:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Run Metadata",
            "",
            f"- Source lines: {report.source_line_count}",
            f"- Extraction retries: {report.retry_count}",
            f"- Meeting date: {meeting_date}",
        ]
    )
    return "\n".join(lines) + "\n"
