"""Pydantic contracts shared by code and Agents."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceSpan(StrictModel):
    start_line: int = Field(ge=1, description="First cited source line number.")
    end_line: int = Field(ge=1, description="Last cited source line number, inclusive.")

    @model_validator(mode="after")
    def validate_order(self) -> EvidenceSpan:
        if self.end_line < self.start_line:
            raise ValueError("end_line must be greater than or equal to start_line")
        return self

    def label(self) -> str:
        if self.start_line == self.end_line:
            return f"L{self.start_line}"
        return f"L{self.start_line}-L{self.end_line}"


class SourceLine(StrictModel):
    number: int = Field(ge=1)
    text: str


class SourceDocument(StrictModel):
    lines: list[SourceLine]
    meeting_date: date | None = None

    @property
    def line_numbers(self) -> frozenset[int]:
        return frozenset(line.number for line in self.lines)

    @property
    def non_empty_line_count(self) -> int:
        return sum(bool(line.text.strip()) for line in self.lines)


class DecisionCandidate(StrictModel):
    id: str = Field(pattern=r"^D[1-9][0-9]*$")
    statement: str = Field(min_length=1)
    classification: Literal["confirmed_decision", "suggestion", "discussion", "unknown"]
    evidence: list[EvidenceSpan] = Field(min_length=1)


class ActionCandidate(StrictModel):
    id: str = Field(pattern=r"^A[1-9][0-9]*$")
    task: str = Field(min_length=1)
    owner: str | None = None
    due_date: str | None = Field(
        default=None,
        description="Exact due-date wording from the source, never an inferred value.",
    )
    commitment: Literal["explicit", "suggested", "uncertain"]
    evidence: list[EvidenceSpan] = Field(min_length=1)


class ExtractionOutput(StrictModel):
    summary: str = Field(min_length=1)
    decisions: list[DecisionCandidate] = Field(default_factory=list)
    actions: list[ActionCandidate] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_ids(self) -> ExtractionOutput:
        ids = [item.id for item in [*self.decisions, *self.actions]]
        if len(ids) != len(set(ids)):
            raise ValueError("candidate IDs must be unique")
        return self


class CandidateReview(StrictModel):
    candidate_id: str = Field(pattern=r"^[DA][1-9][0-9]*$")
    verdict: Literal["pass", "reject", "retry"]
    reason: str = Field(min_length=1)
    missing_fields: list[Literal["owner", "due_date"]] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)


class VerificationOutput(StrictModel):
    reviews: list[CandidateReview] = Field(default_factory=list)
    retry_recommended: bool = False
    feedback: str | None = None

    @model_validator(mode="after")
    def validate_unique_reviews(self) -> VerificationOutput:
        ids = [review.candidate_id for review in self.reviews]
        if len(ids) != len(set(ids)):
            raise ValueError("each candidate must have exactly one review")
        if self.retry_recommended and not self.feedback:
            raise ValueError("retry_recommended requires actionable feedback")
        return self


class EvidenceReference(StrictModel):
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    line_range: str
    text: str


class DecisionRecord(StrictModel):
    id: str
    statement: str
    evidence: list[EvidenceReference]


class ActionRecord(StrictModel):
    id: str
    task: str
    owner: str | None
    due_date: str | None
    status: Literal["confirmed", "needs_clarification"]
    evidence: list[EvidenceReference]


class MeetingActionReport(StrictModel):
    summary: str
    decisions: list[DecisionRecord] = Field(default_factory=list)
    actions: list[ActionRecord] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    retry_count: int = Field(default=0, ge=0, le=1)
    source_line_count: int = Field(default=0, ge=0)
    meeting_date: date | None = None
