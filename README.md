# MinuteFlow

MinuteFlow turns Markdown or plain-text meeting notes into an evidence-grounded report containing confirmed decisions, explicit action items, missing-field questions, and warnings.

The production path uses two OpenAI Agents SDK agents in a deterministic Python workflow:

```text
Intake (code)
  → Extraction Agent
  → Verification Agent
      ├─ pass → Delivery (code)
      └─ retryable → Extraction Agent once → Verification Agent → Delivery
```

Intake, Delivery, routing, and the retry limit are ordinary code. The model never controls the workflow topology.

## Features

- Stable `L1…Ln` source references and verbatim evidence display.
- Pydantic structured outputs for extraction and verification.
- Independent verification before a record can enter the final report.
- Deterministic protection against invented owners, dates, and suggestion-to-decision upgrades.
- At most one extraction retry.
- JSON and Markdown CLI output.
- Offline unit and scenario tests; tests never call an API.
- OpenAI Agents SDK tracing disabled by default for privacy.

## Requirements

- Python 3.11–3.14.
- An OpenAI API key for live meeting processing.

## Install

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
cp .env.example .env
```

Add your API key to `.env`. The file is ignored by Git.

## Run

```bash
.venv/bin/minuteflow examples/meeting.md --format markdown
```

JSON output:

```bash
.venv/bin/minuteflow examples/meeting.md --format json --output outputs/report.json
```

Read from standard input:

```bash
printf 'Team decided to launch Friday.' | .venv/bin/minuteflow -
```

Useful options:

- `--meeting-date YYYY-MM-DD`: supplies meeting-date context without inventing missing dates.
- `--model MODEL_ID`: overrides `MINUTEFLOW_MODEL` for this run.
- `--enable-tracing`: explicitly allows SDK trace export. Traces can contain meeting content.

The default model is `gpt-5.6-luna`, selected for efficient high-volume work. Override it when your account, cost target, or evaluation results require another model.

### Using an OpenAI-compatible endpoint (e.g. DeepSeek)

DeepSeek's API is OpenAI-compatible but does not implement the SDK's
`json_schema` structured outputs, so MinuteFlow switches to JSON mode whenever
`MINUTEFLOW_BASE_URL` is set. JSON mode asks the model for a JSON object and
parses it through the same Pydantic contracts and deterministic checks.

```bash
export MINUTEFLOW_BASE_URL=https://api.deepseek.com
export MINUTEFLOW_MODEL=deepseek-v4-pro
export DEEPSEEK_API_KEY=sk-...
.venv/bin/minuteflow examples/meeting.md --format markdown
```

Prefer putting these values in `.env` (see `.env.example`) rather than exporting
them. Leaving `MINUTEFLOW_BASE_URL` empty keeps the native OpenAI structured-output path.

## Test

```bash
.venv/bin/pytest
.venv/bin/ruff check src tests
```

All automated tests use a scripted Agent backend and therefore need neither an API key nor network access. A live API smoke test is intentionally not run automatically.

## Privacy

- No note is sent anywhere during installation or tests.
- A note is sent to the configured model only when you invoke the live CLI.
- Tracing is off unless `MINUTEFLOW_ENABLE_TRACING=true` or `--enable-tracing` is provided.
- API keys are read from the environment or local `.env` and are never written into reports.

## Project documentation

- Product requirements: `docs/PROJECT.md`
- Architecture: `docs/ARCHITECTURE.md`
- Framework decision: `framework/DECISION.md`
- Agent contracts: `agents/AGENTS.md`
- Workflow: `workflows/WORKFLOW.md`
- Evaluation: `evals/EVALUATION.md`
