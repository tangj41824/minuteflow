---
managed_by: agent-builder
update_mode: auto
version: 8
last_updated: 2026-09-02
project_id: minuteflow
---

# MinuteFlow Status

<!-- AUTO:BEGIN project-status -->

- 当前阶段：0.1.0 独立实现完成；DeepSeek live smoke test 通过；本地 Web 界面（`minuteflow web`）已实现并通过离线验证
- 已完成：Python 包、Pydantic 契约、Intake/Delivery、Extraction/Verification Agents、一次重试 Controller、证据 Guardrails、CLI、示例、评测数据集和自动化测试；JSON mode 兼容路径；证据与澄清问题质量修复；本地 Web 界面（React SPA + FastAPI：粘贴/上传、SSE 实时进度、本地历史与导出）
- 评估结果：60 个离线测试通过（新增事件测试 5 个、Web API 测试 23 个）；Ruff、格式、依赖检查通过；前端 vitest 5 个通过、tsc + vite build 通过；live smoke test 通过
- 隐私状态：测试未调用 API；Tracing 默认关闭；Web 服务默认绑定 127.0.0.1；历史仅存本机 `~/.minuteflow/history/`
- 当前限制：Web 界面尚未用真实 Key 在浏览器里跑 live 验证；尚未用评测数据集做模型质量评测与 Prompt/默认模型调优
- 下一步：浏览器里用 `examples/meeting.md` 跑一次 Web live smoke；按 `evals/TEST_SCENARIOS.md` 用评测数据集做模型质量评测

<!-- AUTO:END project-status -->
