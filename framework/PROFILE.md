---
managed_by: agent-builder
update_mode: auto
version: 2
last_updated: 2026-08-05
project_id: minuteflow
profile: openai-agents-python
implementation_status: offline-tested
---

# MinuteFlow OpenAI Agents SDK Profile

## 1. Profile

- Framework：OpenAI Agents SDK for Python。
- Orchestration：由普通 Python 代码串联两个 Agent 和三个确定性步骤。
- Agent primitives：Extraction、Verification、structured outputs、output guardrail、tracing。
- 不采用：Handoffs、agents-as-tools、Sessions、MCP、长期 Memory、Realtime 和 Voice。

## 2. 实际实现目录

当前外部项目按以下结构实现：

```text
minuteflow/
├── README.md
├── pyproject.toml
├── .env.example
├── src/
│   └── minuteflow/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── exceptions.py
│       ├── renderers.py
│       ├── schemas.py
│       ├── orchestration.py
│       ├── agents/
│       │   ├── backend.py
│       │   ├── extraction.py
│       │   └── verification.py
│       ├── steps/
│       │   ├── intake.py
│       │   └── delivery.py
│       └── guardrails/
│           ├── input.py
│           └── evidence.py
├── tests/
│   ├── unit/
│   └── scenarios/
├── evals/
│   └── datasets/
└── docs/
```

## 3. 蓝图到代码的映射

| 蓝图资产 | 未来代码落点 | 验证方式 |
|---|---|---|
| `agents/AGENTS.md` | `src/minuteflow/agents/` 与 `steps/` | 每个职责只有一个实现责任人 |
| `skills/SKILLS.md` | agents、steps、guardrails 中的单一能力 | 单元测试覆盖每项规则 |
| `workflows/WORKFLOW.md` | `orchestration.py` | 重试计数最多为 1，停止条件确定 |
| `docs/ARCHITECTURE.md` | `schemas.py` 与模块边界 | Schema 能表达空字段、证据和警告 |
| `evals/TEST_SCENARIOS.md` | `tests/scenarios/`、`evals/datasets/` | 三类场景结果与禁止行为都可复现 |

## 4. 最小依赖边界

- 只引入 OpenAI Agents SDK、Schema/测试所需依赖和一个经确认的模型适配。
- 不因框架可用而启用 Handoff、Session、MCP、Memory 或托管工具。
- 模型名称、Provider 和密钥不写入蓝图；使用环境变量和 `.env.example` 说明。
- Intake、Delivery 和重试控制保持确定性，避免不必要的 token 消耗。

## 5. 已确认的实施选择

- Python：3.11–3.14。
- Framework：`openai-agents>=0.19.4,<0.20`。
- Provider：OpenAI；默认模型 `gpt-5.6-luna`，允许环境变量覆盖。
- 入口：CLI。
- Tracing：默认关闭，仅显式启用。
- 实现目录：`minuteflow`。
