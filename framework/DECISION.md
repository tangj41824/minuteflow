---
managed_by: agent-builder
update_mode: auto
version: 3
last_updated: 2026-08-05
project_id: minuteflow
decision_status: implemented-and-offline-tested
selected_profile: openai-agents-python
confidence: high
---

# MinuteFlow Framework Decision

## 1. 需求信号

| 维度 | 强度 | MinuteFlow 需要 |
|---|---:|---|
| 流程拓扑 | 2 | 固定顺序；只有一次受控的 Extraction → Verification 回退 |
| 状态与恢复 | 0 | 单次短任务；不需要持久 checkpoint、暂停恢复或长时运行 |
| 协作方式 | 1 | 两个语义角色顺序协作；不需要共享群聊、动态选人或自治团队 |
| 人工介入 | 0 | 只在最终报告中提出澄清问题，不在运行中等待批准 |
| 数据能力 | 0 | 单份本地文本；不需要 RAG、长期 Memory、MCP 或外部 Connector |
| 输出与安全 | 2 | 需要结构化记录、输入检查、证据 Guardrail、Tracing 和可评测输出 |
| 复杂度预算 | 2 | 必须保持轻量；不能为三个测试场景引入图服务或多 Agent 消息基础设施 |

## 2. Must 条件

- Python 中可表达结构化输出和独立验证角色。
- 主流程由代码确定，重试上限不能交给模型自由决定。
- 能对输入与输出增加 Guardrail，并保留运行轨迹供后续评测。
- 不要求数据库、持久状态服务、群聊路由或 YAML 角色系统。

## 3. 候选比较

| Profile | 适配度 | 复杂度 | 结论 | 主要依据 |
|---|---|---|---|---|
| OpenAI Agents SDK | 高 | 低到中 | 采用 | Python-first、结构化输出、Guardrails、Tracing 和 code orchestration 正好覆盖需要 |
| Minimal Python Pipeline | 中高 | 最低 | 备选 | 可以完成流程，但 Agent 运行、Guardrail 与 Tracing 需要自行建立 |
| LangGraph | 低 | 中高 | 排除 | 项目没有 durable state、复杂分支、checkpoint 或运行中恢复需求 |
| AgentScope | 低 | 高 | 排除 | 项目不需要消息式 Agent 团队、Memory、RAG 或完整多 Agent 基础设施 |
| AutoGen AgentChat | 低 | 中高 | 排除 | 项目没有共享群聊、动态 speaker、Swarm 或运行中人工反馈 |
| CrewAI | 中低 | 中 | 排除 | 固定提取管线不需要 role/task YAML 或自治 Crew；角色抽象会增加配置 |

## 4. 选择

- 选定 Profile：OpenAI Agents SDK for Python。
- 编排方式：代码驱动 sequential pipeline，不让 LLM 自行决定流程拓扑。
- 实际 Agent：Extraction Agent、Verification Agent。
- 确定性组件：Intake、Delivery、retry controller。
- 决策置信度：高。

OpenAI Agents SDK 比手写 Minimal Pipeline 多提供当前确实需要的结构化 Agent 输出、Guardrail 和 Tracing，又不要求图运行时。它也允许 Intake 与 Delivery 保持普通 Python 组件，因此不会因为逻辑上有四个职责就强制产生四次模型调用。

## 5. 未选原因

- 不选 LangGraph：一次有限回退不构成引入持久状态图的充分理由。
- 不选 AgentScope 或 AutoGen：没有动态团队协作或共享消息上下文。
- 不选 CrewAI：任务不是角色自治型业务 Crew，YAML agent/task 配置不会提升核心质量。
- Minimal Pipeline 保留为退出路径：如果实际实现不需要 SDK Tracing 或 Agent primitive，可以在不改变数据契约和测试场景的情况下退回普通 Python。

## 6. 仍待实施时确认

- 具体 Python 版本、模型 Provider、模型 ID、密钥管理和 CLI/API 入口仍需在真正写代码前确认。
- 如果用户要求非 Python 实现，本选择必须重新评估，不能机械迁移。

## 7. 重新选型触发条件

- 需要跨任务持久状态、暂停恢复或人工批准点时，重新比较 LangGraph。
- 需要动态多 Agent 会话时，重新比较 AgentScope 与 AutoGen。
- 需要角色化自治团队或复杂业务自动化时，重新比较 CrewAI。
- 如果只保留单次模型调用且无需 SDK Tracing，退回 Minimal Pipeline。
