---
managed_by: agent-builder
update_mode: auto
version: 3
last_updated: 2026-08-05
project_id: minuteflow
---

# MinuteFlow Architecture

## 1. 架构概述

MinuteFlow 使用一个确定性 Controller 串联四个逻辑职责。Extraction 与 Verification 是 OpenAI Agents SDK Agent；Intake、Delivery 和 Controller 是普通 Python 组件。Controller 负责顺序、重试上限和状态，不负责语义判断。

```text
Input
  → Intake
  → Extraction Agent
  → Verification Agent
      ├─ pass → Delivery → Output
      └─ fail → Extraction Agent（最多一次）→ Verification Agent
```

四个逻辑职责不等于四个独立进程或四次模型调用。Profile 明确只让需要语义判断的 Extraction 和 Verification 调用 Agent runtime。

## 2. 模块与职责

| 模块 | 类型 | 单一职责 |
|---|---|---|
| Controller | 确定性控制器 | 保存状态、调用顺序、一次重试上限和终止条件 |
| Intake | 确定性组件 | 验证输入、规范化文本、生成稳定行号和段落 |
| Extraction Agent | OpenAI Agents SDK Agent | 产生结构化决策和行动项候选，不决定候选是否可信 |
| Verification Agent | OpenAI Agents SDK Agent | 对照原文检查证据、类别、负责人、日期和冲突 |
| Delivery | 确定性组件 | 只渲染验证通过的记录，并输出待确认问题与警告 |

## 3. 共享状态

| 字段 | 内容 | 写入者 | 读取者 |
|---|---|---|---|
| `source_lines` | 带稳定行号的原始文本 | Intake | Extraction、Verification、Delivery |
| `candidate_decisions` | 决策候选及证据行号 | Extraction | Verification |
| `candidate_actions` | 行动候选及字段、证据行号 | Extraction | Verification |
| `verification_results` | 通过、拒绝、缺失字段和原因 | Verification | Controller、Delivery |
| `retry_count` | 已执行的重新提取次数 | Controller | Controller |
| `clarification_questions` | 需要用户补充的信息 | Verification | Delivery |
| `final_report` | 最终结构化报告 | Delivery | 调用方 |

## 4. 关键输出契约

### DecisionRecord

- `statement`：已确认决定。
- `id`：稳定候选 ID。
- `evidence`：至少一个包含行号范围和原文的 `EvidenceReference`。

### ActionRecord

- `task`：明确动作。
- `owner`：字符串或空值。
- `due_date`：原文日期表达或空值。
- `status`：`confirmed` 或 `needs_clarification`。
- `evidence`：行号范围和原文。

### MeetingActionReport

- `summary`
- `decisions[]`
- `actions[]`
- `clarification_questions[]`
- `warnings[]`
- `errors[]`
- `retry_count`
- `source_line_count`

## 5. 失败处理

- 空输入：Intake 终止流程，Delivery 输出输入错误，不调用 Extraction。
- 无候选：属于正常结果，直接输出空列表。
- 无效行号：SDK Output Guardrail 与 Controller 的二次检查关闭流程。
- 证据不支持：Verification 拒绝候选，Delivery 不会重新加入。
- 存在可修正的分类问题：Controller 将验证反馈返回 Extraction，最多一次。
- 重试后仍失败：删除失败候选，保留警告，不阻塞其他有效结果。

## 6. 关键决策

- 使用确定性主流程，避免让一个自主 Agent 自由决定所有步骤。
- 把证据验证与提取分离，减少同一 Agent 自我确认错误。
- 选择 OpenAI Agents SDK 的 code orchestration、structured outputs、Guardrails 与 Tracing；不启用 Handoff、Session、MCP 或长期 Memory。
- 不引入长期记忆、向量库、外部 Connector 或复杂编排框架。
- 相对日期没有会议日期时保留原文，不计算绝对日期。

## 7. 实际代码映射

| 责任 | 实现 |
|---|---|
| 数据契约 | `src/minuteflow/schemas.py` |
| Intake | `src/minuteflow/steps/intake.py` |
| Extraction Agent | `src/minuteflow/agents/extraction.py` |
| Verification Agent | `src/minuteflow/agents/verification.py` |
| SDK Backend | `src/minuteflow/agents/backend.py` |
| Controller | `src/minuteflow/orchestration.py` |
| Delivery | `src/minuteflow/steps/delivery.py` |
| CLI 与渲染 | `src/minuteflow/cli.py`、`src/minuteflow/renderers.py` |

## 8. 实现分离边界

业务代码已经在独立 MinuteFlow 项目中实现，Agent Builder 内仍只保留蓝图和实施结果摘要。当前实现使用 Python 3.11+、OpenAI Agents SDK 0.19.x、可配置模型和 CLI 入口。
