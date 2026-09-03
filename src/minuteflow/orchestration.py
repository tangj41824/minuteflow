"""Deterministic MinuteFlow orchestration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime

from minuteflow.agents.backend import AgentBackend
from minuteflow.exceptions import AgentContractError, InputValidationError, MinuteFlowError
from minuteflow.guardrails.evidence import (
    AgentRunContext,
    extraction_contract_issues,
    verification_contract_issues,
)
from minuteflow.schemas import MeetingActionReport, PipelineEvent, PipelineStage
from minuteflow.steps.delivery import deliver_report
from minuteflow.steps.intake import intake_notes

EventCallback = Callable[[PipelineEvent], Awaitable[None]]


class MinuteFlowPipeline:
    """Code-controlled pipeline with a single bounded retry.

    ``on_event`` is an optional observer hook: it reports pipeline progress to
    callers (e.g. the web UI) without influencing routing, retries, or delivery.
    Every run with a callback ends in exactly one ``delivered`` or ``failed`` event.
    """

    def __init__(self, backend: AgentBackend, *, max_input_chars: int = 100_000) -> None:
        self.backend = backend
        self.max_input_chars = max_input_chars

    async def run(
        self,
        text: str,
        *,
        meeting_date: date | None = None,
        on_event: EventCallback | None = None,
    ) -> MeetingActionReport:
        async def emit(
            stage: PipelineStage,
            *,
            retry_count: int = 0,
            message: str | None = None,
        ) -> None:
            if on_event is None:
                return
            await on_event(
                PipelineEvent(
                    stage=stage,
                    timestamp=datetime.now(UTC),
                    retry_count=retry_count,
                    message=message,
                )
            )

        await emit("started")
        try:
            document = intake_notes(
                text,
                meeting_date=meeting_date,
                max_input_chars=self.max_input_chars,
            )
        except InputValidationError as exc:
            # Invalid input is a delivered outcome, not a failure: no model call
            # happens, and the report carries the error message.
            await emit("delivered")
            return MeetingActionReport(
                summary="The input could not be processed.",
                errors=[str(exc)],
                meeting_date=meeting_date,
            )

        retry_count = 0
        feedback: str | None = None
        try:
            with self.backend.trace_context():
                while True:
                    await emit("extracting", retry_count=retry_count)
                    extraction = await self.backend.extract(document, feedback=feedback)
                    extraction_issues = extraction_contract_issues(
                        AgentRunContext(valid_line_numbers=document.line_numbers), extraction
                    )
                    if extraction_issues:
                        raise AgentContractError("; ".join(extraction_issues))

                    candidate_ids = frozenset(
                        item.id for item in [*extraction.decisions, *extraction.actions]
                    )
                    await emit("verifying", retry_count=retry_count)
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

                    has_retry_review = any(
                        review.verdict == "retry" for review in verification.reviews
                    )
                    if retry_count == 0 and verification.retry_recommended and has_retry_review:
                        retry_count = 1
                        feedback = verification.feedback
                        await emit(
                            "retrying",
                            retry_count=retry_count,
                            message="Verification requested one extraction retry.",
                        )
                        continue
                    break
        except MinuteFlowError as exc:
            await emit("failed", retry_count=retry_count, message=str(exc))
            raise

        await emit("delivered", retry_count=retry_count)
        return deliver_report(
            document,
            extraction,
            verification,
            retry_count=retry_count,
        )
