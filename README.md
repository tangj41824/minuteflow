# MinuteFlow

[English](#minuteflow) | [中文](#minuteflow中文)

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
- Evaluation: `evals/TEST_SCENARIOS.md`

---

# MinuteFlow（中文）

MinuteFlow 将 Markdown 或纯文本会议记录转化为一份有证据支撑的报告，包含已确认的决策、明确的行动项、缺失字段的追问和告警。

生产路径使用 OpenAI Agents SDK 的两个 Agent，运行在确定性的 Python 工作流中：

```text
Intake（代码）
  → Extraction Agent（提取）
  → Verification Agent（验证）
      ├─ 通过 → Delivery（代码）
      └─ 可重试 → Extraction Agent 再跑一次 → Verification Agent → Delivery
```

Intake、Delivery、路由和重试上限都是普通代码，模型永远不能控制工作流的拓扑结构。

## 功能特性

- 稳定的 `L1…Ln` 行号引用与原文（verbatim）证据展示。
- Extraction 与 Verification 均使用 Pydantic 结构化输出。
- 任何记录进入最终报告前都必须经过独立验证。
- 确定性防护，杜绝编造负责人、日期，以及把"建议"升级成"决策"。
- 提取环节最多重试一次。
- CLI 支持 JSON 与 Markdown 两种输出格式。
- 离线单元与场景测试；测试从不调用 API。
- OpenAI Agents SDK tracing 默认关闭，保护隐私。

## 环境要求

- Python 3.11–3.14。
- 一个 OpenAI API Key（用于实时处理会议记录）。

## 安装

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
cp .env.example .env
```

把 API Key 填入 `.env`。该文件已被 Git 忽略。

## 运行

```bash
.venv/bin/minuteflow examples/meeting.md --format markdown
```

JSON 输出：

```bash
.venv/bin/minuteflow examples/meeting.md --format json --output outputs/report.json
```

从标准输入读取：

```bash
printf 'Team decided to launch Friday.' | .venv/bin/minuteflow -
```

常用选项：

- `--meeting-date YYYY-MM-DD`：提供会议日期上下文，避免凭空补日期。
- `--model MODEL_ID`：覆盖本次运行的 `MINUTEFLOW_MODEL`。
- `--enable-tracing`：显式允许 SDK 导出 trace。trace 可能包含会议内容。

默认模型为 `gpt-5.6-luna`，面向大批量处理的高效率场景。可根据账号、成本目标或评测结果更换模型。

### 使用 OpenAI 兼容端点（例如 DeepSeek）

DeepSeek 的 API 兼容 OpenAI，但不支持 SDK 的 `json_schema` 结构化输出。因此只要设置了 `MINUTEFLOW_BASE_URL`，MinuteFlow 就会切换到 JSON mode：要求模型返回 JSON 对象，再经过同一套 Pydantic 契约和确定性检查完成解析。

```bash
export MINUTEFLOW_BASE_URL=https://api.deepseek.com
export MINUTEFLOW_MODEL=deepseek-v4-pro
export DEEPSEEK_API_KEY=sk-...
.venv/bin/minuteflow examples/meeting.md --format markdown
```

建议把这些值放在 `.env`（见 `.env.example`）而不是 export。`MINUTEFLOW_BASE_URL` 留空则保持原生 OpenAI 结构化输出路径。

## 测试

```bash
.venv/bin/pytest
.venv/bin/ruff check src tests
```

所有自动化测试都使用脚本化的 Agent backend，因此不需要 API Key，也不需要联网。live API smoke test 有意不自动执行。

## 隐私

- 安装和测试过程中不会把任何笔记发送出去。
- 只有当你主动运行 live CLI 时，笔记才会发送给你所配置的模型。
- 除非设置 `MINUTEFLOW_ENABLE_TRACING=true` 或提供 `--enable-tracing`，否则 tracing 保持关闭。
- API Key 只从环境变量或本地 `.env` 读取，绝不会写入报告。

## 项目文档

- 产品需求：`docs/PROJECT.md`
- 架构：`docs/ARCHITECTURE.md`
- 框架选型：`framework/DECISION.md`
- Agent 契约：`agents/AGENTS.md`
- 工作流：`workflows/WORKFLOW.md`
- 评测：`evals/TEST_SCENARIOS.md`
