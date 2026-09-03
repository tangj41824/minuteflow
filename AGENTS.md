# MinuteFlow Repository Instructions

MinuteFlow is an evidence-grounded meeting-note action planner. Preserve the deterministic workflow and privacy boundary when modifying this repository.

## Read first

1. `docs/PROJECT.md`
2. `framework/DECISION.md`
3. `docs/ARCHITECTURE.md`
4. `agents/AGENTS.md`
5. `workflows/WORKFLOW.md`
6. `evals/TEST_SCENARIOS.md`

## Architecture invariants

- Intake, Delivery, and retry control remain deterministic Python code.
- Only Extraction and Verification are model Agents.
- Every final decision or action has valid source-line evidence.
- Missing owner or due date stays null and produces a clarification question.
- Suggestions and discussions never become confirmed outcomes.
- Extraction may retry at most once after Verification feedback.
- The web layer (`src/minuteflow/web/`) is a second caller of the same pipeline; it never changes pipeline topology. Local run history uses plain JSON files — not a database.
- Do not add Memory, RAG, Handoffs, external Connectors, or a database without a new framework decision.

## Privacy and external actions

- Never commit `.env`, API keys, meeting notes, or generated private reports.
- Do not run live API tests unless the user explicitly authorizes the data, model cost, and call.
- OpenAI Agents SDK tracing remains disabled by default because traces can contain note content.
- The web server binds 127.0.0.1 by default; history stores notes and reports locally under `~/.minuteflow/history/`. Never commit `frontend/dist`, `node_modules`, or any history content.
- Automated tests must remain fully offline.

## Verification

Run before declaring implementation work complete:

```bash
.venv/bin/pytest
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
.venv/bin/python -m pip check
```

Update `docs/STATUS.md` when verified behavior changes. Keep live model evidence separate from scripted-backend evidence.
