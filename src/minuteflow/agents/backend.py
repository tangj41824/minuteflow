"""Agent backend abstraction and OpenAI Agents SDK implementation."""

from __future__ import annotations

import os
import re
from contextlib import AbstractContextManager
from typing import Any, Protocol, TypeVar

from openai import AsyncOpenAI
from pydantic import ValidationError

from agents import (
    OutputGuardrailTripwireTriggered,
    Runner,
    set_default_openai_client,
    set_tracing_disabled,
    trace,
)
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


_T = TypeVar("_T")
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def parse_json_object(raw: str, output_type: type[_T], *, label: str) -> _T:
    """Parse a model's free-text JSON response into a Pydantic contract.

    Used for OpenAI-compatible providers (e.g. DeepSeek) that support JSON mode
    (``response_format={"type": "json_object"}``) but not SDK structured outputs.
    """
    match = _JSON_OBJECT_RE.search(raw or "")
    if match is None:
        raise AgentContractError(f"{label} did not return a JSON object.")
    try:
        return output_type.model_validate_json(match.group(0))
    except ValidationError as exc:
        raise AgentContractError(f"{label} returned invalid JSON: {exc}") from exc


class OpenAIAgentsBackend:
    """Run the two semantic roles with the OpenAI Agents SDK.

    When ``settings.base_url`` is set, the backend targets an OpenAI-compatible
    endpoint (such as DeepSeek) and uses JSON mode plus deterministic parsing
    because those providers do not implement SDK ``json_schema`` structured
    outputs. Otherwise it keeps the native structured-output path.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.json_mode = settings.base_url is not None
        set_tracing_disabled(not settings.enable_tracing)
        if settings.base_url:
            # The OpenAI client enforces credentials at construction time, so use a
            # placeholder when no key is present. `_require_api_key` still blocks any
            # live call before data is sent.
            key = settings.api_key or os.getenv("OPENAI_API_KEY") or "missing-api-key"
            client = AsyncOpenAI(api_key=key, base_url=settings.base_url)
            set_default_openai_client(client, use_for_tracing=False)
        self.extraction_agent = build_extraction_agent(
            settings.model, settings.reasoning_effort, json_mode=self.json_mode
        )
        self.verification_agent = build_verification_agent(
            settings.model, settings.reasoning_effort, json_mode=self.json_mode
        )

    def _require_api_key(self) -> None:
        key = self.settings.api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ConfigurationError(
                "An API key is required for live processing. Set OPENAI_API_KEY for OpenAI, "
                "or DEEPSEEK_API_KEY / MINUTEFLOW_API_KEY for an OpenAI-compatible endpoint. "
                "Add it to .env or the shell environment. Automated tests do not need a key."
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
        if self.json_mode:
            output = parse_json_object(output, ExtractionOutput, label="Extraction Agent")
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
        if self.json_mode:
            output = parse_json_object(output, VerificationOutput, label="Verification Agent")
        if not isinstance(output, VerificationOutput):
            raise AgentContractError("Verification Agent returned an unexpected output type.")
        return output
