"""Deterministic MinuteFlow orchestration."""

from __future__ import annotations

from datetime import date

from minuteflow.agents.backend import AgentBackend
from minuteflow.exceptions import AgentContractError, InputValidationError
from minuteflow.guardrails.evidence import (
    AgentRunContext,
    extraction_contract_issues,
    verification_contract_issues,
)
from minuteflow.schemas import MeetingActionReport
from minuteflow.steps.delivery import deliver_report
from minuteflow.steps.intake import intake_notes


class MinuteFlowPipeline:
    """Code-controlled pipeline with a single bounded retry."""

    def __init__(self, backend: AgentBackend, *, max_input_chars: int = 100_000) -> None:
        self.backend = backend
        self.max_input_chars = max_input_chars

    async def run(
        self,
        text: str,
        *,
        meeting_date: date | None = None,
    ) -> MeetingActionReport:
        try:
            document = intake_notes(
                text,
                meeting_date=meeting_date,
                max_input_chars=self.max_input_chars,
            )
        except InputValidationError as exc:
            return MeetingActionReport(
                summary="The input could not be processed.",
                errors=[str(exc)],
                meeting_date=meeting_date,
            )

        retry_count = 0
        feedback: str | None = None
        with self.backend.trace_context():
            while True:
                extraction = await self.backend.extract(document, feedback=feedback)
                extraction_issues = extraction_contract_issues(
                    AgentRunContext(valid_line_numbers=document.line_numbers), extraction
                )
                if extraction_issues:
                    raise AgentContractError("; ".join(extraction_issues))

                candidate_ids = frozenset(
                    item.id for item in [*extraction.decisions, *extraction.actions]
                )
                verification = await self.backend.verify(document, extraction)
                verification_issues = verification_contract_issues(
                    AgentRunContext(
                        valid_line_numbers=document.line_numbers,
                        candidate_ids=candidate_ids,
                    ),
                    verification,
                )
                if verification_issues:
                    raise AgentContractError("; ".join(verification_issues))

                has_retry_review = any(review.verdict == "retry" for review in verification.reviews)
                if retry_count == 0 and verification.retry_recommended and has_retry_review:
                    retry_count = 1
                    feedback = verification.feedback
                    continue
                break

        return deliver_report(
            document,
            extraction,
            verification,
            retry_count=retry_count,
        )
