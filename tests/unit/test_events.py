from __future__ import annotations

import pytest

from minuteflow.exceptions import AgentContractError
from minuteflow.orchestration import MinuteFlowPipeline
from minuteflow.schemas import (
    CandidateReview,
    DecisionCandidate,
    EvidenceSpan,
    ExtractionOutput,
    PipelineEvent,
    VerificationOutput,
)
from tests.helpers import ScriptedBackend


def _ship_extraction(classification: str = "confirmed_decision") -> ExtractionOutput:
    return ExtractionOutput(
        summary="A release decision was made.",
        decisions=[
            DecisionCandidate(
                id="D1",
                statement="Ship on Friday.",
                classification=classification,
                evidence=[EvidenceSpan(start_line=1, end_line=1)],
            )
        ],
    )


@pytest.mark.asyncio
async def test_success_run_emits_ordered_events() -> None:
    source = "The team decided to ship on Friday."
    backend = ScriptedBackend(
        extractions=[_ship_extraction()],
        verifications=[
            VerificationOutput(
                reviews=[
                    CandidateReview(candidate_id="D1", verdict="pass", reason="Direct evidence.")
                ]
            )
        ],
    )
    events: list[PipelineEvent] = []

    async def collect(event: PipelineEvent) -> None:
        events.append(event)

    report = await MinuteFlowPipeline(backend).run(source, on_event=collect)

    assert [event.stage for event in events] == [
        "started",
        "extracting",
        "verifying",
        "delivered",
    ]
    assert all(event.retry_count == 0 for event in events)
    timestamps = [event.timestamp for event in events]
    assert timestamps == sorted(timestamps)
    assert report.errors == []


@pytest.mark.asyncio
async def test_retry_run_emits_retrying_event() -> None:
    source = "The team decided to ship on Friday."
    backend = ScriptedBackend(
        extractions=[_ship_extraction("unknown"), _ship_extraction()],
        verifications=[
            VerificationOutput(
                reviews=[
                    CandidateReview(
                        candidate_id="D1",
                        verdict="retry",
                        reason="Use the full statement and correct classification.",
                    )
                ],
                retry_recommended=True,
                feedback="Classify D1 as a confirmed decision and preserve Friday.",
            ),
            VerificationOutput(
                reviews=[
                    CandidateReview(candidate_id="D1", verdict="pass", reason="Direct evidence.")
                ]
            ),
        ],
    )
    events: list[PipelineEvent] = []

    async def collect(event: PipelineEvent) -> None:
        events.append(event)

    report = await MinuteFlowPipeline(backend).run(source, on_event=collect)

    assert [event.stage for event in events] == [
        "started",
        "extracting",
        "verifying",
        "retrying",
        "extracting",
        "verifying",
        "delivered",
    ]
    assert [event.retry_count for event in events] == [0, 0, 0, 1, 1, 1, 1]
    assert events[3].message is not None
    assert report.retry_count == 1


@pytest.mark.asyncio
async def test_empty_input_delivers_without_model_calls() -> None:
    backend = ScriptedBackend(extractions=[], verifications=[])
    events: list[PipelineEvent] = []

    async def collect(event: PipelineEvent) -> None:
        events.append(event)

    report = await MinuteFlowPipeline(backend).run(" \n", on_event=collect)

    assert [event.stage for event in events] == ["started", "delivered"]
    assert report.errors == ["The meeting notes are empty."]
    assert backend.extract_calls == backend.verify_calls == 0


@pytest.mark.asyncio
async def test_contract_failure_emits_failed_and_raises() -> None:
    extraction = ExtractionOutput(
        summary="Summary",
        decisions=[
            DecisionCandidate(
                id="D1",
                statement="Unsupported",
                classification="confirmed_decision",
                evidence=[EvidenceSpan(start_line=99, end_line=99)],
            )
        ],
    )
    backend = ScriptedBackend(extractions=[extraction], verifications=[])
    events: list[PipelineEvent] = []

    async def collect(event: PipelineEvent) -> None:
        events.append(event)

    with pytest.raises(AgentContractError, match="unavailable"):
        await MinuteFlowPipeline(backend).run("Only one line", on_event=collect)

    assert [event.stage for event in events] == ["started", "extracting", "failed"]
    assert events[-1].message is not None and "unavailable" in events[-1].message
    assert backend.verify_calls == 0


@pytest.mark.asyncio
async def test_no_callback_keeps_existing_behavior() -> None:
    source = "The team decided to ship on Friday."
    backend = ScriptedBackend(
        extractions=[_ship_extraction()],
        verifications=[
            VerificationOutput(
                reviews=[
                    CandidateReview(candidate_id="D1", verdict="pass", reason="Direct evidence.")
                ]
            )
        ],
    )

    report = await MinuteFlowPipeline(backend).run(source)

    assert report.decisions[0].statement == "Ship on Friday."
