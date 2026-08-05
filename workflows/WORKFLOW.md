---
managed_by: agent-builder
update_mode: auto
version: 3
last_updated: 2026-08-05
project_id: minuteflow
---

# MinuteFlow Workflow

## 1. 触发条件

调用方提交一份会议纪要文本，可选提供会议日期。

## 2. 主流程

1. Controller 建立空状态，设置 `retry_count = 0`。
2. Intake Agent 验证输入并生成稳定行号。
3. 输入为空时直接进入 Delivery Agent，输出错误和空列表。
4. Extraction Agent 生成决策与行动候选。
5. Verification Agent 对照原文逐条检查。
6. 若全部候选通过或只存在不可修正的无证据候选，进入 Delivery Agent。
7. 若存在可能通过重新分类或修正行号解决的问题，且 `retry_count = 0`，Controller 将验证反馈返回 Extraction Agent，并把计数改为 1。
8. Verification Agent 再检查一次；仍失败的候选被删除并记录警告。
9. Delivery Agent 输出最终报告。

当前实现由 `src/minuteflow/orchestration.py` 负责整个顺序与重试；Extraction 和 Verification 分别由 Runner 调用，Intake、Delivery 与计数器不交给模型控制。

## 3. 路由规则

| 条件 | 路由 |
|---|---|
| 输入为空 | Intake → Delivery |
| 没有决策或行动候选 | Extraction → Verification → Delivery |
| 所有候选有直接证据 | Verification → Delivery |
| 存在可修正问题且尚未重试 | Verification → Extraction |
| 已重试或问题不可修正 | Verification → Delivery，拒绝失败候选 |

## 4. 检查点

- Intake 后：原文是否完整、行号是否稳定。
- Extraction 后：候选是否都有证据引用和明确类型。
- Verification 后：证据是否真的支持结论，缺失字段是否保持空值。
- Delivery 后：最终报告是否只包含通过记录。

## 5. 结束条件

- 生成一个符合 `MeetingActionReport` 契约的结果；或
- 输入无效时生成带错误信息的空结果。

流程不得因没有行动项而失败，也不得超过一次重新提取。
