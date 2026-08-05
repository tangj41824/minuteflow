---
managed_by: agent-builder
update_mode: auto
version: 2
last_updated: 2026-08-05
project_id: minuteflow
---

# MinuteFlow Test Scenarios

以下三类场景已经在 `tests/scenarios/test_core_scenarios.py` 自动化；机器可读索引位于 `evals/datasets/scenarios.json`。

## Scenario 1：明确决定和行动项

### 输入

```text
L1 # 产品周会
L2 团队决定将 beta 发布从 8 月 12 日推迟到 8 月 19 日。
L3 Mina 会在 8 月 15 日前更新 onboarding 文档。
L4 Leo 负责检查支付日志，但会议没有确定完成日期。
L5 下周再讨论定价。
```

### 预期路径

Intake → Extraction → Verification → Delivery，不需要重试。

### 预期输出

- 决策：beta 发布改为 8 月 19 日，证据 `L2`。
- 行动：Mina 更新 onboarding 文档，截止 8 月 15 日，证据 `L3`。
- 行动：Leo 检查支付日志，`due_date = null`，证据 `L4`。
- 待确认：Leo 的完成日期。
- `L5` 只是未来讨论，不是已确认决定或行动。

### 禁止行为

- 不得为 Leo 推断截止日期。
- 不得把“下周讨论定价”写成定价决定。

## Scenario 2：建议和模糊责任

### 输入

```text
L1 # 增长讨论
L2 大家觉得也许应该在下周检查一次新用户数据。
L3 Alex 提到预算可能需要调整，但没有形成决定。
```

### 预期路径

Intake → Extraction → Verification → Delivery；允许 Verification 拒绝候选，不要求重试。

### 预期输出

- `decisions = []`。
- `actions = []`，因为没有明确承诺或负责人。
- 待确认：是否要把数据检查转为行动项、由谁负责、何时完成。
- 可选警告：预算调整仍处于讨论状态。

### 禁止行为

- 不得把 Alex 写成预算调整负责人。
- 不得把“下周”转换为具体日期。
- 不得把建议写成团队决定。

## Scenario 3：没有结果的正常输入

### 输入

```text
L1 # 灵感讨论
L2 讨论了几个可能的活动主题。
L3 下次会议继续收集想法。
```

### 预期路径

Intake → Extraction → Verification → Delivery。

### 预期输出

- `decisions = []`。
- `actions = []`。
- 报告说明没有发现已确认决策或明确行动项。

### 禁止行为

- 不得为了填充报告而生成行动项。
- 不得把“继续收集想法”自动分配给未知人员。
