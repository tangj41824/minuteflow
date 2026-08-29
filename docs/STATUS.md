---
managed_by: agent-builder
update_mode: auto
version: 7
last_updated: 2026-08-29
project_id: minuteflow
---

# MinuteFlow Status

<!-- AUTO:BEGIN project-status -->

- 当前阶段：0.1.0 独立实现完成；已用真实 DeepSeek API Key 完成 live smoke test，JSON mode 端到端验证通过
- 已完成：Python 包、Pydantic 契约、Intake/Delivery、Extraction/Verification Agents、一次重试 Controller、证据 Guardrails、CLI、示例、评测数据集和自动化测试；`MINUTEFLOW_BASE_URL` / `DEEPSEEK_API_KEY` 配置与 JSON mode（`json_object`）解析路径；证据文本改为 verbatim（修复 `L3: L3:` 重复）；澄清问题改为每个缺失字段一条确定性生成（修复重复与 `.?` 瑕疵）
- 评估结果：32 个离线测试通过（新增 2 个）；Ruff、格式、依赖和 CLI 检查通过；live smoke test 通过（提取/验证/交付与护栏行为符合预期）
- 隐私状态：测试未调用 API；Tracing 默认关闭；live 测试仅发送非敏感样例 `examples/meeting.md`
- 当前限制：live 验证仅覆盖单个样例；尚未用评测数据集做模型质量评测与 Prompt/默认模型调优
- 下一步：按 `evals/TEST_SCENARIOS.md` 用评测数据集跑一次模型质量评测，再决定是否调整默认模型或 Prompt

<!-- AUTO:END project-status -->
