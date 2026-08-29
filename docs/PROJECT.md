---
managed_by: agent-builder
update_mode: auto
version: 6
last_updated: 2026-08-29
project_id: minuteflow
status: implementation-live-tested
delivery_scope: runnable-python-cli
export_status: implementation-complete
---

# MinuteFlow — Meeting Notes Action Planner

## 1. 项目概述

MinuteFlow 接收一份 Markdown 或纯文本会议纪要，提取已经形成的决策和明确承诺的行动项，为每条结果保留原文证据，并把缺少负责人、日期或结论的信息标记为待确认。

MinuteFlow 是一个可安装的 Python CLI。它不需要外部 SaaS、数据库、长期记忆或图形界面；只有用户主动运行 CLI 时才会把纪要发送给所配置的模型。

## 2. 要解决的问题

会议纪要经常混合事实、建议、讨论、决定和承诺。人工整理时容易漏掉行动项，也可能把“有人建议”错误写成“团队已经决定”。MinuteFlow 应只输出有原文依据的结果，不替用户编造负责人或截止日期。

## 3. 输入与输出

### 输入

- 一份 UTF-8 Markdown 或纯文本会议纪要。
- 可选会议日期，用于解释“下周”等相对时间；没有日期时不得猜测绝对日期。

### 输出

- 会议主题摘要。
- 已确认决策列表。
- 行动项列表：任务、负责人、截止日期、状态、原文证据。
- 待确认问题列表。
- 处理警告，例如输入为空或证据冲突。

## 4. 当前范围

- 单次处理一份纪要。
- 保留稳定的行号证据，例如 `L3-L4`。
- 区分已决定、明确行动、建议、讨论和未知信息。
- 每个候选结果经过独立验证后才能进入最终输出。
- 最多执行一次基于验证反馈的重新提取，避免无限循环。

## 5. 非目标

- 不读取日历、邮件、录音或视频。
- 不自动发送任务或修改第三方系统。
- 不做跨会议长期记忆。
- 不生成复杂前端或设计稿。

## 6. 实现交付边界

- 当前交付：可安装 Python 包、OpenAI Agents SDK 双 Agent 编排、CLI、JSON/Markdown 输出、离线测试、示例和完整设计文档。
- 当前不交付：Web UI、HTTP API、托管部署、第三方任务系统写入或长期记忆。
- 数据边界：安装和测试不会发送纪要；实时 CLI 运行需要用户配置 `OPENAI_API_KEY`，Tracing 默认关闭。

## 7. 核心规则

1. 任何决策或行动项都必须引用输入中的一个或多个行号。
2. “建议、考虑、可能、以后讨论”等表达不能自动升级为已确认决策。
3. 没有明确负责人时，`owner` 必须为空并生成待确认问题。
4. 没有明确截止日期时，`due_date` 必须为空；不得根据常识推断。
5. 验证失败的记录不能进入最终结果，除非一次重试后获得直接证据。
6. 正常的空结果是允许的；不得为了显得有用而虚构行动项。

## 8. 验收标准

| ID | 标准 | 优先级 | 验证方法 | 通过条件 |
|---|---|---|---|---|
| MF-01 | Agent 职责清晰且不重复 | Must | 交叉检查 `agents/AGENTS.md` 与 `workflows/WORKFLOW.md` | 每个阶段只有一个最终责任人，输入输出契约明确 |
| MF-02 | 每条结果都有原文证据 | Must | 运行自动化场景和 Guardrail 测试 | 决策和行动项均有有效行号；无效行号关闭流程 |
| MF-03 | 不编造负责人或日期 | Must | 使用歧义场景 | 未明确的字段保持空值，并生成待确认问题 |
| MF-04 | 验证失败存在有限回退 | Must | 检查 Workflow 路由 | 最多重试一次，之后删除无证据候选并继续 |
| MF-05 | 支持正常、歧义和空结果 | Must | 运行 `tests/scenarios/` | 三类场景及空输入均通过 |
| MF-06 | 架构保持最小复杂度 | Must | 模块审查 | 两个模型 Agent、三个确定性组件，无数据库或外部 Connector |
| FW-01 | 框架选择有需求证据 | Must | 检查 `framework/DECISION.md` | 比较主要候选，记录采用、排除和重新选型条件 |
| DIR-01 | 实现目录职责清晰 | Must | 检查项目树 | 根目录只有标准入口与配置；源码、测试、评测和设计资料分区 |
| HND-01 | 独立实现可运行 | Must | 安装包并运行 CLI/测试 | 隔离环境可安装，CLI 可启动，离线测试全部通过 |
| IMPL-01 | Agent SDK 契约可执行 | Must | 运行 Agent 定义与输出契约测试 | 两个 Agent 都有 Pydantic output type 和输出 Guardrail |
| PRIV-01 | 测试与 Tracing 默认安全 | Must | 清除 API Key 后运行测试与 CLI 检查 | 测试不调用 API；Tracing 默认关闭；缺少 Key 时安全失败 |
