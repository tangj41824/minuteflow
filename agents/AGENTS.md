---
managed_by: agent-builder
update_mode: auto
version: 2
last_updated: 2026-08-05
project_id: minuteflow
---

# MinuteFlow Agents

## 1. Intake Agent

- 实现类型：确定性 Python step，不调用模型。
- 职责：验证输入、规范化换行、保留原文、生成稳定的 `L1...Ln` 行号并识别基本段落结构。
- 输入：原始会议纪要、可选会议日期。
- 输出：`source_lines`、`segments`、输入警告。
- Skills：Line Indexing、Input Validation。
- 完成条件：每个非空原文行都有稳定编号；原文内容未被改写。
- 禁止：提取决策、猜测日期、删除看似无关的原文。

## 2. Extraction Agent

- 实现类型：OpenAI Agents SDK Agent，使用结构化输出。
- 职责：识别决策和明确行动候选，并为每个候选附上证据行号。
- 输入：`source_lines`、`segments`、可选验证反馈。
- 输出：`candidate_decisions`、`candidate_actions`。
- Skills：Decision/Action Extraction、Uncertainty Normalization。
- 完成条件：每个候选都标明类型、字段和证据；建议与讨论不会被直接标成已确认决定。
- 禁止：自行判定候选最终通过、补全缺失负责人或日期。

## 3. Verification Agent

- 实现类型：独立 OpenAI Agents SDK Agent，并由输出 Guardrail 约束。
- 职责：逐条检查候选是否被原文支持，核对类型、行号、负责人、日期、冲突和不确定表达。
- 输入：原文、候选决策、候选行动。
- 输出：通过记录、拒绝记录、拒绝原因、缺失字段和待确认问题。
- Skills：Evidence Grounding、Ambiguity Detection。
- 完成条件：每个候选都有明确结果；无证据候选被拒绝；缺失字段保持空值。
- 禁止：重写原文以迁就候选、用常识补全字段、直接格式化最终报告。

## 4. Delivery Agent

- 实现类型：确定性 Python step，不调用模型。
- 职责：把验证通过的记录渲染成稳定报告，同时呈现待确认问题和警告。
- 输入：原文索引、验证结果、输入警告。
- 输出：`MeetingActionReport`。
- Skills：Structured Report Rendering。
- 完成条件：最终报告只包含通过记录；空结果被清楚表达；证据可回看。
- 禁止：重新加入被拒绝候选、创造新事实、隐藏缺失字段。

## 协作边界

- Agent 之间只通过已定义状态字段交接，不共享未记录的临时结论。
- Controller 决定是否重试；Extraction Agent 和 Verification Agent 都不能自行无限循环。
- Verification Agent 是记录能否进入最终输出的唯一责任人。
- Delivery Agent 是最终格式的唯一责任人。
