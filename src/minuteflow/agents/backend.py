"""Agent backend abstraction and OpenAI Agents SDK implementation."""

from __future__ import annotations

import os
from contextlib import AbstractContextManager
from typing import Any, Protocol

from agents import OutputGuardrailTripwireTriggered, Runner, set_tracing_disabled, trace
from minuteflow.agents.extraction import build_extraction_agent, build_extraction_prompt
from minuteflow.agents.verification import build_verification_agent, build_verification_prompt
from minuteflow.config import Settings
from minuteflow.exceptions import AgentContractError, AgentRuntimeError, ConfigurationError
from minuteflow.guardrails.evidence import AgentRunContext
from minuteflow.schemas import ExtractionOutput, SourceDocument, VerificationOutput


class AgentBackend(Protocol):
    def trace_context(self) -> AbstractContextManager[Any]: ...

    async def extract(
        self, document: SourceDocument, *, feedback: str | None = None
    ) -> ExtractionOutput: ...

    async def verify(
        self, document: SourceDocument, extraction: ExtractionOutput
    ) -> VerificationOutput: ...


class OpenAIAgentsBackend:
    """Run the two semantic roles with the OpenAI Agents SDK."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        set_tracing_disabled(not settings.enable_tracing)
        self.extraction_agent = build_extraction_agent(settings.model, settings.reasoning_effort)
        self.verification_agent = build_verification_agent(
            settings.model, settings.reasoning_effort
        )

    def _require_api_key(self) -> None:
        if not os.getenv("OPENAI_API_KEY"):
            raise ConfigurationError(
                "OPENAI_API_KEY is required for live processing. Add it to .env or the shell "
                "environment. Automated tests do not need a key."
            )

    def trace_context(self) -> AbstractContextManager[Any]:
        return trace("MinuteFlow meeting action planner")

    async def extract(
        self, document: SourceDocument, *, feedback: str | None = None
    ) -> ExtractionOutput:
        self._require_api_key()
        context = AgentRunContext(valid_line_numbers=document.line_numbers)
        try:
            result = await Runner.run(
                self.extraction_agent,
                build_extraction_prompt(document, feedback),
                context=context,
            )
        except OutputGuardrailTripwireTriggered as exc:
            info = exc.guardrail_result.output.output_info
            raise AgentContractError(f"Extraction evidence guardrail failed: {info}") from exc
        except Exception as exc:
            raise AgentRuntimeError(f"Extraction Agent failed: {exc}") from exc
        output = result.final_output
        if not isinstance(output, ExtractionOutput):
            raise AgentContractError("Extraction Agent returned an unexpected output type.")
        return output

    async def verify(
        self, document: SourceDocument, extraction: ExtractionOutput
    ) -> VerificationOutput:
        self._require_api_key()
        candidate_ids = frozenset(item.id for item in [*extraction.decisions, *extraction.actions])
        context = AgentRunContext(
            valid_line_numbers=document.line_numbers,
            candidate_ids=candidate_ids,
        )
        try:
            result = await Runner.run(
                self.verification_agent,
                build_verification_prompt(document, extraction),
                context=context,
            )
        except OutputGuardrailTripwireTriggered as exc:
            info = exc.guardrail_result.output.output_info
            raise AgentContractError(f"Verification coverage guardrail failed: {info}") from exc
        except Exception as exc:
            raise AgentRuntimeError(f"Verification Agent failed: {exc}") from exc
        output = result.final_output
        if not isinstance(output, VerificationOutput):
            raise AgentContractError("Verification Agent returned an unexpected output type.")
        return output
