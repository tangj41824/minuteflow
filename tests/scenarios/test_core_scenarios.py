from __future__ import annotations

import json
from pathlib import Path

import pytest

from minuteflow.exceptions import AgentContractError
from minuteflow.orchestration import MinuteFlowPipeline
from minuteflow.schemas import (
    ActionCandidate,
    CandidateReview,
    DecisionCandidate,
    EvidenceSpan,
    ExtractionOutput,
    VerificationOutput,
)
from tests.helpers import ScriptedBackend


@pytest.mark.asyncio
async def test_clear_decision_and_actions() -> None:
    source = """# Product weekly
The team decided to move the beta release to August 19.
Mina will update the onboarding guide by August 15.
Leo is responsible for checking payment logs.
Pricing will be discussed next week."""
    extraction = ExtractionOutput(
        summary="The team changed the beta date and assigned two follow-up actions.",
        decisions=[
            DecisionCandidate(
                id="D1",
                statement="Move the beta release to August 19.",
                classification="confirmed_decision",
                evidence=[EvidenceSpan(start_line=2, end_line=2)],
            )
        ],
        actions=[
            ActionCandidate(
                id="A1",
                task="Update the onboarding guide.",
                owner="Mina",
                due_date="August 15",
                commitment="explicit",
                evidence=[EvidenceSpan(start_line=3, end_line=3)],
            ),
            ActionCandidate(
                id="A2",
                task="Check payment logs.",
                owner="Leo",
                due_date=None,
                commitment="explicit",
                evidence=[EvidenceSpan(start_line=4, end_line=4)],
            ),
        ],
    )
    verification = VerificationOutput(
        reviews=[
            CandidateReview(candidate_id="D1", verdict="pass", reason="Direct decision."),
            CandidateReview(candidate_id="A1", verdict="pass", reason="Direct assignment."),
            CandidateReview(
                candidate_id="A2",
                verdict="pass",
                reason="Direct assignment without a due date.",
                missing_fields=["due_date"],
                clarification_questions=["When should Leo finish checking payment logs?"],
            ),
        ]
    )
    backend = ScriptedBackend(extractions=[extraction], verifications=[verification])

    report = await MinuteFlowPipeline(backend).run(source)

    assert [decision.id for decision in report.decisions] == ["D1"]
    assert [action.id for action in report.actions] == ["A1", "A2"]
    assert report.actions[0].status == "confirmed"
    assert report.actions[1].due_date is None
    assert report.actions[1].status == "needs_clarification"
    assert report.decisions[0].evidence[0].line_range == "L2"
    assert report.decisions[0].evidence[0].text == (
        "The team decided to move the beta release to August 19."
    )
    assert report.clarification_questions == ["When is this action due: Check payment logs?"]
    assert backend.extract_calls == backend.verify_calls == 1


@pytest.mark.asyncio
async def test_duplicate_model_questions_collapse_into_one_deterministic_question() -> None:
    source = "Pat will ship the release notes by Friday."
    extraction = ExtractionOutput(
        summary="One action with an owner but no due date.",
        actions=[
            ActionCandidate(
                id="A1",
                task="Ship the release notes.",
                owner="Pat",
                due_date=None,
                commitment="explicit",
                evidence=[EvidenceSpan(start_line=1, end_line=1)],
            )
        ],
    )
    verification = VerificationOutput(
        reviews=[
            CandidateReview(
                candidate_id="A1",
                verdict="pass",
                reason="Explicit task without a due date.",
                missing_fields=["due_date"],
                clarification_questions=[
                    "When is the release-notes task due?",
                    "When is the release-notes task due?",
                ],
            )
        ],
    )
    backend = ScriptedBackend(extractions=[extraction], verifications=[verification])

    report = await MinuteFlowPipeline(backend).run(source)

    assert report.clarification_questions == ["When is this action due: Ship the release notes?"]
    assert report.actions[0].evidence[0].text == "Pat will ship the release notes by Friday."


@pytest.mark.asyncio
async def test_question_artifact_periods_are_normalized() -> None:
    source = "Maybe we should inspect the logs."
    extraction = ExtractionOutput(
        summary="A suggestion.",
        actions=[
            ActionCandidate(
                id="A1",
                task="Inspect the logs.",
                owner=None,
                due_date=None,
                commitment="suggested",
                evidence=[EvidenceSpan(start_line=1, end_line=1)],
            )
        ],
    )
    verification = VerificationOutput(
        reviews=[
            CandidateReview(
                candidate_id="A1",
                verdict="reject",
                reason="Not an explicit commitment.",
                clarification_questions=["Should this become an action: Inspect the logs.?"],
            )
        ],
    )
    backend = ScriptedBackend(extractions=[extraction], verifications=[verification])

    report = await MinuteFlowPipeline(backend).run(source)

    assert report.clarification_questions == ["Should this become an action: Inspect the logs?"]


@pytest.mark.asyncio
async def test_suggestions_do_not_become_results() -> None:
    source = """# Growth discussion
Maybe we should inspect new-user data next week.
Alex said the budget might need adjustment, but no decision was made."""
    extraction = ExtractionOutput(
        summary="The group discussed possible data and budget follow-ups.",
        decisions=[
            DecisionCandidate(
                id="D1",
                statement="Adjust the budget.",
                classification="suggestion",
                evidence=[EvidenceSpan(start_line=3, end_line=3)],
            )
        ],
        actions=[
            ActionCandidate(
                id="A1",
                task="Inspect new-user data.",
                owner=None,
                due_date="next week",
                commitment="suggested",
                evidence=[EvidenceSpan(start_line=2, end_line=2)],
            )
        ],
    )
    verification = VerificationOutput(
        reviews=[
            CandidateReview(candidate_id="D1", verdict="reject", reason="Not decided."),
            CandidateReview(
                candidate_id="A1",
                verdict="reject",
                reason="No explicit commitment or owner.",
                clarification_questions=[
                    "Should data inspection become an action, and who owns it?"
                ],
            ),
        ]
    )
    backend = ScriptedBackend(extractions=[extraction], verifications=[verification])

    report = await MinuteFlowPipeline(backend).run(source)

    assert report.decisions == []
    assert report.actions == []
    assert report.clarification_questions == [
        "Should data inspection become an action, and who owns it?"
    ]
    assert any("No confirmed" in warning for warning in report.warnings)


@pytest.mark.asyncio
async def test_normal_empty_result() -> None:
    source = "# Ideas\nThe group discussed several possible campaign themes."
    backend = ScriptedBackend(
        extractions=[
            ExtractionOutput(summary="The meeting was exploratory and produced no commitments.")
        ],
        verifications=[VerificationOutput()],
    )

    report = await MinuteFlowPipeline(backend).run(source)

    assert report.decisions == []
    assert report.actions == []
    assert report.errors == []
    assert any("No confirmed" in warning for warning in report.warnings)


@pytest.mark.asyncio
async def test_pipeline_retries_extraction_only_once() -> None:
    source = "The team decided to ship on Friday."
    first = ExtractionOutput(
        summary="A release decision was discussed.",
        decisions=[
            DecisionCandidate(
                id="D1",
                statement="Ship.",
                classification="unknown",
                evidence=[EvidenceSpan(start_line=1, end_line=1)],
            )
        ],
    )
    second = ExtractionOutput(
        summary="The team decided to ship Friday.",
        decisions=[
            DecisionCandidate(
                id="D1",
                statement="Ship on Friday.",
                classification="confirmed_decision",
                evidence=[EvidenceSpan(start_line=1, end_line=1)],
            )
        ],
    )
    backend = ScriptedBackend(
        extractions=[first, second],
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

    report = await MinuteFlowPipeline(backend).run(source)

    assert report.retry_count == 1
    assert [decision.statement for decision in report.decisions] == ["Ship on Friday."]
    assert backend.extract_calls == backend.verify_calls == 2
    assert backend.feedback_received == [
        None,
        "Classify D1 as a confirmed decision and preserve Friday.",
    ]


@pytest.mark.asyncio
async def test_ungrounded_owner_is_removed() -> None:
    source = "Review the incident logs before Friday."
    extraction = ExtractionOutput(
        summary="An action was recorded without an owner.",
        actions=[
            ActionCandidate(
                id="A1",
                task="Review the incident logs.",
                owner="Alex",
                due_date="Friday",
                commitment="explicit",
                evidence=[EvidenceSpan(start_line=1, end_line=1)],
            )
        ],
    )
    verification = VerificationOutput(
        reviews=[CandidateReview(candidate_id="A1", verdict="pass", reason="Task is explicit.")]
    )
    backend = ScriptedBackend(extractions=[extraction], verifications=[verification])

    report = await MinuteFlowPipeline(backend).run(source)

    assert report.actions[0].owner is None
    assert report.actions[0].due_date == "Friday"
    assert report.actions[0].status == "needs_clarification"
    assert any("owner was removed" in warning for warning in report.warnings)


@pytest.mark.asyncio
async def test_invalid_evidence_fails_closed() -> None:
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

    with pytest.raises(AgentContractError, match="unavailable"):
        await MinuteFlowPipeline(backend).run("Only one line")
    assert backend.verify_calls == 0


@pytest.mark.asyncio
async def test_empty_input_stops_before_agents() -> None:
    backend = ScriptedBackend(extractions=[], verifications=[])

    report = await MinuteFlowPipeline(backend).run(" \n")

    assert report.errors == ["The meeting notes are empty."]
    assert backend.extract_calls == backend.verify_calls == 0


def test_eval_dataset_contains_three_required_classes() -> None:
    dataset_path = Path(__file__).parents[2] / "evals" / "datasets" / "scenarios.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    assert {case["class"] for case in dataset["cases"]} == {
        "clear",
        "ambiguous",
        "empty-result",
    }
