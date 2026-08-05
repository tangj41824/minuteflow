from minuteflow.agents.extraction import build_extraction_agent
from minuteflow.agents.verification import build_verification_agent
from minuteflow.guardrails.evidence import (
    AgentRunContext,
    extraction_contract_issues,
    verification_contract_issues,
)
from minuteflow.schemas import (
    CandidateReview,
    DecisionCandidate,
    EvidenceSpan,
    ExtractionOutput,
    VerificationOutput,
)


def test_sdk_agents_have_structured_outputs_and_guardrails() -> None:
    extraction_agent = build_extraction_agent("gpt-5.6-luna", "low")
    verification_agent = build_verification_agent("gpt-5.6-luna", "low")

    assert extraction_agent.output_type is not None
    assert verification_agent.output_type is not None
    assert len(extraction_agent.output_guardrails) == 1
    assert len(verification_agent.output_guardrails) == 1


def test_evidence_contract_detects_unknown_lines() -> None:
    output = ExtractionOutput(
        summary="Summary",
        decisions=[
            DecisionCandidate(
                id="D1",
                statement="Ship",
                classification="confirmed_decision",
                evidence=[EvidenceSpan(start_line=9, end_line=9)],
            )
        ],
    )
    issues = extraction_contract_issues(
        AgentRunContext(valid_line_numbers=frozenset({1, 2})), output
    )
    assert issues and "unavailable" in issues[0]


def test_verification_contract_requires_every_candidate() -> None:
    output = VerificationOutput(
        reviews=[CandidateReview(candidate_id="D1", verdict="pass", reason="Supported")]
    )
    issues = verification_contract_issues(
        AgentRunContext(
            valid_line_numbers=frozenset({1}),
            candidate_ids=frozenset({"D1", "A1"}),
        ),
        output,
    )
    assert issues == ["Missing reviews for candidate IDs: ['A1']"]
