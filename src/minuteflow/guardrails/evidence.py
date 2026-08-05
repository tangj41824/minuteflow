"""Evidence and review coverage guardrails."""

from __future__ import annotations

from dataclasses import dataclass

from agents.decorators import output_guardrail

from agents import Agent, GuardrailFunctionOutput, RunContextWrapper
from minuteflow.schemas import EvidenceSpan, ExtractionOutput, VerificationOutput


@dataclass(frozen=True, slots=True)
class AgentRunContext:
    valid_line_numbers: frozenset[int]
    candidate_ids: frozenset[str] = frozenset()


def _span_issues(span: EvidenceSpan, valid_line_numbers: frozenset[int]) -> list[str]:
    referenced = set(range(span.start_line, span.end_line + 1))
    missing = sorted(referenced - valid_line_numbers)
    if not missing:
        return []
    return [f"{span.label()} references unavailable lines: {missing}"]


def extraction_contract_issues(context: AgentRunContext, output: ExtractionOutput) -> list[str]:
    issues: list[str] = []
    for candidate in [*output.decisions, *output.actions]:
        for span in candidate.evidence:
            issues.extend(
                f"{candidate.id}: {issue}"
                for issue in _span_issues(span, context.valid_line_numbers)
            )
    return issues


def verification_contract_issues(context: AgentRunContext, output: VerificationOutput) -> list[str]:
    reviewed = {review.candidate_id for review in output.reviews}
    missing = sorted(context.candidate_ids - reviewed)
    unexpected = sorted(reviewed - context.candidate_ids)
    issues: list[str] = []
    if missing:
        issues.append(f"Missing reviews for candidate IDs: {missing}")
    if unexpected:
        issues.append(f"Unexpected candidate IDs in reviews: {unexpected}")
    return issues


@output_guardrail
async def extraction_output_guardrail(
    context: RunContextWrapper[AgentRunContext],
    agent: Agent[AgentRunContext],
    output: ExtractionOutput,
) -> GuardrailFunctionOutput:
    del agent
    issues = extraction_contract_issues(context.context, output)
    return GuardrailFunctionOutput(output_info={"issues": issues}, tripwire_triggered=bool(issues))


@output_guardrail
async def verification_output_guardrail(
    context: RunContextWrapper[AgentRunContext],
    agent: Agent[AgentRunContext],
    output: VerificationOutput,
) -> GuardrailFunctionOutput:
    del agent
    issues = verification_contract_issues(context.context, output)
    return GuardrailFunctionOutput(output_info={"issues": issues}, tripwire_triggered=bool(issues))
