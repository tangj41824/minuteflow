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


def _references(document: SourceDocument, spans: list[EvidenceSpan]) -> list[EvidenceReference]:
    by_number = {line.number: line.text for line in document.lines}
    references: list[EvidenceReference] = []
    for span in spans:
        text = "\n".join(
            f"L{number}: {by_number[number]}"
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
    if field == "owner":
        return f"Who owns this action: {action.task}?"
    return f"When is this action due: {action.task}?"


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
        questions.extend(review.clarification_questions if review else [])
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
        clarification_questions=_unique(questions),
        warnings=_unique(warnings),
        retry_count=retry_count,
        source_line_count=len(document.lines),
        meeting_date=document.meeting_date,
    )
