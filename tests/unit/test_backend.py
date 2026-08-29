import pytest

from minuteflow.agents.backend import OpenAIAgentsBackend, parse_json_object
from minuteflow.agents.extraction import build_extraction_agent
from minuteflow.agents.verification import build_verification_agent
from minuteflow.config import Settings
from minuteflow.exceptions import AgentContractError, ConfigurationError
from minuteflow.schemas import ExtractionOutput, VerificationOutput


def test_parse_json_object_accepts_plain_json() -> None:
    raw = '{"summary": "ok", "decisions": [], "actions": [], "warnings": []}'
    output = parse_json_object(raw, ExtractionOutput, label="Extraction Agent")
    assert isinstance(output, ExtractionOutput)
    assert output.summary == "ok"


def test_parse_json_object_accepts_code_fenced_json() -> None:
    raw = (
        "Here is the result:\n```json\n"
        '{"summary": "ok", "decisions": [], "actions": [], "warnings": []}\n```'
    )
    output = parse_json_object(raw, ExtractionOutput, label="Extraction Agent")
    assert output.summary == "ok"


def test_parse_json_object_rejects_non_json() -> None:
    with pytest.raises(AgentContractError, match="did not return a JSON object"):
        parse_json_object("no json here", ExtractionOutput, label="Extraction Agent")


def test_parse_json_object_rejects_invalid_contract() -> None:
    with pytest.raises(AgentContractError, match="invalid JSON"):
        parse_json_object(
            '{"summary": "ok", "decisions": [{"id": "D1"}]}',
            ExtractionOutput,
            label="Extraction Agent",
        )


def test_json_mode_extraction_agent_drops_structured_output() -> None:
    agent = build_extraction_agent("deepseek-v4-pro", "low", json_mode=True)
    assert agent.output_type is None
    assert agent.output_guardrails == []
    assert "json" in agent.instructions.lower()
    assert agent.model_settings.extra_body == {"response_format": {"type": "json_object"}}


def test_json_mode_verification_agent_drops_structured_output() -> None:
    agent = build_verification_agent("deepseek-v4-pro", "low", json_mode=True)
    assert agent.output_type is None
    assert agent.output_guardrails == []
    assert "json" in agent.instructions.lower()
    assert agent.model_settings.extra_body == {"response_format": {"type": "json_object"}}


def test_backend_selects_json_mode_from_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    native = OpenAIAgentsBackend(Settings(model="gpt-5.6-luna", base_url=None))
    compatible = OpenAIAgentsBackend(
        Settings(model="deepseek-v4-pro", base_url="https://api.deepseek.com")
    )

    assert native.json_mode is False
    assert compatible.json_mode is True


def test_backend_requires_api_key_before_live_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    backend = OpenAIAgentsBackend(Settings(model="gpt-5.6-luna"))

    with pytest.raises(ConfigurationError, match="API key is required"):
        backend._require_api_key()


def test_parse_json_object_handles_verification_schema() -> None:
    raw = (
        '{"reviews": [{"candidate_id": "D1", "verdict": "pass", "reason": "Supported."}],'
        '"retry_recommended": false, "feedback": null}'
    )
    output = parse_json_object(raw, VerificationOutput, label="Verification Agent")
    assert isinstance(output, VerificationOutput)
    assert output.reviews[0].candidate_id == "D1"
