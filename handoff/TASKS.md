---
managed_by: agent-builder
update_mode: auto
version: 3
last_updated: 2026-08-05
project_id: minuteflow
implementation_status: completed-offline
---

# MinuteFlow Implementation Tasks

四项任务已在独立实现目录完成。下列记录保留目标、验证和完成证据。

## Task 1：建立外部实现仓库与数据契约（完成）

- 目标：在用户确认的外部目录建立独立项目，并把 `DecisionRecord`、`ActionRecord` 和 `MeetingActionReport` 转为所选语言的可验证 Schema。
- 输入：`docs/PROJECT.md`、`docs/ARCHITECTURE.md`、`framework/PROFILE.md`、`evals/TEST_SCENARIOS.md`。
- 输出：独立仓库、Schema、三个场景 fixture。
- 验证：Schema 能表达空负责人、空截止日期、证据行号和警告。
- 完成条件：外部仓库有独立版本历史，Agent Builder 内没有业务源码。
- 完成证据：`pyproject.toml`、`src/minuteflow/schemas.py`、`evals/datasets/scenarios.json`。

## Task 2：实现 Intake 与 Extraction（完成）

- 目标：实现输入验证、稳定行号和决策/行动候选提取。
- 输入：Task 1 的 Schema 与 fixture。
- 输出：Intake、Extraction 和候选记录。
- 验证：Scenario 1 产生正确候选；Scenario 2 的建议保留不确定标签；原文不被改写。
- 完成条件：候选都有有效证据范围，且没有自动补全负责人或日期。
- 完成证据：`steps/intake.py`、`agents/extraction.py`、`guardrails/input.py`、契约测试。

## Task 3：实现 Verification、一次回退与 Delivery（完成）

- 目标：实现证据验证、有限重试、失败候选删除和稳定报告输出。
- 输入：Task 2 候选和原文。
- 输出：通过/拒绝结果与最终报告。
- 验证：伪造行号候选必须被拒绝；重试计数不能超过 1；空结果正常完成。
- 完成条件：三个测试场景符合预期行为，最终输出不包含被拒绝记录。
- 完成证据：`agents/verification.py`、`orchestration.py`、`steps/delivery.py` 和场景测试。

## Task 4：建立框架行为测试与最小入口（完成）

- 目标：为三个场景建立自动化行为测试，并提供一个最小入口处理单份文本。
- 输入：前三项实现。
- 输出：测试套件和 CLI、API 或其他经用户确认的单一入口。
- 验证：正常、歧义、空结果和空输入测试全部通过。
- 完成条件：运行说明可在干净环境复现；将结果摘要回写到本框架的 `evals/EVALUATION.md`，但业务代码仍留在外部仓库。
- 完成证据：19 个离线测试通过；CLI、Ruff、格式和依赖检查通过；`README.md` 包含安装与运行说明。
