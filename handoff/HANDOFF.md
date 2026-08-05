---
managed_by: agent-builder
update_mode: auto
version: 4
last_updated: 2026-08-05
project_id: minuteflow
handoff_status: implementation-completed-offline
target_directory: minuteflow
---

# MinuteFlow Implementation Handoff

## 1. 当前边界

MinuteFlow 已在 `minuteflow` 完成独立 Python 实现。Agent Builder 继续只保存蓝图和实施摘要，业务源码不回流。

## 2. 已确认的实施选择

1. 实现目录：`minuteflow`。
2. Python：3.11–3.14。
3. Framework：OpenAI Agents SDK 0.19.x；默认模型 `gpt-5.6-luna`，可配置。
4. 入口：CLI；JSON 和 Markdown 输出。
5. 隐私：API Key 从环境读取，Tracing 默认关闭，自动化测试使用离线替身。

用户仍需自行提供 API Key 才能执行 live 模型调用；项目不会在测试中读取或使用它。

## 3. 实现资产

- `README.md`
- `docs/PROJECT.md`
- `docs/ARCHITECTURE.md`
- `framework/DECISION.md`
- `framework/PROFILE.md`
- `agents/AGENTS.md`
- `skills/SKILLS.md`
- `workflows/WORKFLOW.md`
- `evals/TEST_SCENARIOS.md`
- `handoff/TASKS.md`
- `references/SELECTED_REFERENCES.md`
- `pyproject.toml`、`.env.example`、`.gitignore`
- `src/minuteflow/`
- `tests/unit/`、`tests/scenarios/`
- `evals/datasets/`
- `examples/meeting.md`

## 4. 实施规则

- 外部目录必须是独立项目根目录，不能位于 `Agent_Builder/projects/`。
- 实现过程中发现的框架缺陷可以摘要回写 Builder，但源码、依赖和构建产物不回流。
- 没有实际运行证据前，`evals/EVALUATION.md` 只记录框架评估；代码测试结果必须明确标注来源仓库与版本。
- Live 模型结果和离线测试必须分别记录，不能把 scripted backend 结果写成真实模型质量。

## 5. 导出记录

- 复制方式：保留 Builder 内源蓝图，同时创建外部副本；没有移动或删除源文件。
- 2026-08-05：蓝图重构为标准分层目录并增加框架决策与实现 Profile；外部副本同步使用相同结构。
- 2026-08-05：完成 0.1.0 Python CLI、双 Agent SDK 编排、Guardrails、19 个离线测试和独立运行说明。
- 当前状态：离线实现通过；等待用户 API Key 后进行可选 live smoke test。
