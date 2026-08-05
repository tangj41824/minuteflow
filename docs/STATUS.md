---
managed_by: agent-builder
update_mode: auto
version: 5
last_updated: 2026-08-05
project_id: minuteflow
---

# MinuteFlow Status

<!-- AUTO:BEGIN project-status -->

- 当前阶段：0.1.0 独立实现完成并通过离线验证
- 已完成：Python 包、Pydantic 契约、Intake/Delivery、Extraction/Verification Agents、一次重试 Controller、证据 Guardrails、CLI、示例、评测数据集和自动化测试
- 评估结果：19 个离线测试通过；Ruff、格式、依赖和 CLI 检查通过
- 实现目录：`minuteflow`
- 隐私状态：测试未调用 API；Tracing 默认关闭；无 Key 的实时运行会在发送数据前失败
- 当前限制：没有使用真实 API Key 执行模型质量 smoke test
- 下一步：用户配置自己的 API Key 后用非敏感样例运行一次 live smoke test，再决定是否调整默认模型或 Prompt

<!-- AUTO:END project-status -->
