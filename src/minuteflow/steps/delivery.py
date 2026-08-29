"""Build a grounded final report from verified candidates."""

from __future__ import annotations

import re
from collections.abc import Iterable

from minuteflow.schemas import (
    ActionCandidate,
    ActionRecord,
    CandidateReview,
    DecisionRecord,
    EvidenceReference,
    EvidenceSpan,
    ExtractionOutput,
    MeetingActionReport,
    SourceDocument,
    VerificationOutput,
)

_HEDGE_PATTERN = re.compile(
    r"(?:也许|可能|建议|考虑|以后讨论|下次讨论|再讨论|未形成决定|"
    r"\bmaybe\b|\bmight\b|\bcould\b|\bsuggest(?:ed|ion)?\b|\bconsider(?:ed|ing)?\b)",
    re.IGNORECASE,
)


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value.strip() for value in values if value and value.strip()))


_QUESTION_ARTIFACT_RE = re.compile(r"\.\s*\?$")


def _unique_questions(values: Iterable[str]) -> list[str]:
    cleaned = (_QUESTION_ARTIFACT_RE.sub("?", value.strip()) for value in values)
    return list(dict.fromkeys(question for question in cleaned if question))


def _references(document: SourceDocument, spans: list[EvidenceSpan]) -> list[EvidenceReference]:
    """Build evidence references with verbatim source text; line numbers live in ``line_range``."""
    by_number = {line.number: line.text for line in document.lines}
    references: list[EvidenceReference] = []
    for span in spans:
        text = "\n".join(
            by_number[number]
            for number in range(span.start_line, span.end_line + 1)
            if number in by_number
        )
        references.append(
            EvidenceReference(
                start_line=span.start_line,
                end_line=span.end_line,
                line_range=span.label(),
                text=text,
            )
        )
    return references


def _evidence_text(document: SourceDocument, spans: list[EvidenceSpan]) -> str:
    by_number = {line.number: line.text for line in document.lines}
    return "\n".join(
        by_number[number]
        for span in spans
        for number in range(span.start_line, span.end_line + 1)
        if number in by_number
    )


def _question_for(action: ActionCandidate, field: str) -> str:
    task = action.task.rstrip(" .")
    if field == "owner":
        return f"Who owns this action: {task}?"
    return f"When is this action due: {task}?"


def _is_pass(review: CandidateReview | None) -> bool:
    return bool(review and review.verdict == "pass")


def deliver_report(
    document: SourceDocument,
    extraction: ExtractionOutput,
    verification: VerificationOutput,
    *,
    retry_count: int,
) -> MeetingActionReport:
    reviews = {review.candidate_id: review for review in verification.reviews}
    decisions: list[DecisionRecord] = []
    actions: list[ActionRecord] = []
    warnings = list(extraction.warnings)
    questions: list[str] = []

    for candidate in extraction.decisions:
        review = reviews.get(candidate.id)
        evidence_text = _evidence_text(document, candidate.evidence)
        if not _is_pass(review):
            if review and review.verdict == "retry":
                warnings.append(
                    f"{candidate.id} remained retryable after the retry limit and was removed."
                )
            continue
        if candidate.classification != "confirmed_decision" or _HEDGE_PATTERN.search(evidence_text):
            warnings.append(
                f"{candidate.id} was removed because its evidence is not a confirmed decision."
            )
            continue
        decisions.append(
            DecisionRecord(
                id=candidate.id,
                statement=candidate.statement,
                evidence=_references(document, candidate.evidence),
            )
        )

    for candidate in extraction.actions:
        review = reviews.get(candidate.id)
        evidence_text = _evidence_text(document, candidate.evidence)
        if not _is_pass(review):
            if review and review.verdict == "retry":
                warnings.append(
                    f"{candidate.id} remained retryable after the retry limit and was removed."
                )
            if review:
                questions.extend(review.clarification_questions)
            continue
        if candidate.commitment != "explicit" or _HEDGE_PATTERN.search(evidence_text):
            warnings.append(
                f"{candidate.id} was removed because its evidence is not an explicit commitment."
            )
            questions.extend(review.clarification_questions if review else [])
            continue

        owner = candidate.owner
        due_date = candidate.due_date
        if owner and owner.casefold() not in evidence_text.casefold():
            warnings.append(
                f"{candidate.id} owner was removed because it is absent from the evidence."
            )
            owner = None
        if due_date and due_date.casefold() not in evidence_text.casefold():
            warnings.append(
                f"{candidate.id} due date was removed because it is absent from the evidence."
            )
            due_date = None

        missing = set(review.missing_fields if review else [])
        if owner is None:
            missing.add("owner")
        if due_date is None:
            missing.add("due_date")
        # In-report candidates get exactly one deterministic question per missing field;
        # model phrasing is dropped here to avoid near-duplicate questions.
        questions.extend(_question_for(candidate, field) for field in sorted(missing))

        actions.append(
            ActionRecord(
                id=candidate.id,
                task=candidate.task,
                owner=owner,
                due_date=due_date,
                status="needs_clarification" if missing else "confirmed",
                evidence=_references(document, candidate.evidence),
            )
        )

    if not decisions and not actions:
        warnings.append("No confirmed decisions or explicit action items were found.")

    return MeetingActionReport(
        summary=extraction.summary,
        decisions=decisions,
        actions=actions,
        clarification_questions=_unique_questions(questions),
        warnings=_unique(warnings),
        retry_count=retry_count,
        source_line_count=len(document.lines),
        meeting_date=document.meeting_date,
    )
