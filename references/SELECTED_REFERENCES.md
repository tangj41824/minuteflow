---
managed_by: agent-builder
update_mode: auto
version: 3
last_updated: 2026-08-05
project_id: minuteflow
---

# MinuteFlow Selected References

| 本地参考 | 选用内容 | 使用位置 | 采用方式 |
|---|---|---|---|
| `references/openai-agents-python/examples/agent_patterns/deterministic.py` | 用代码控制固定 Agent 顺序 | `src/minuteflow/orchestration.py` | 已按模式原创实现，不复制示例代码 |
| `references/openai-agents-python/examples/agent_patterns/output_guardrails.py` | 最终输出进入交付前进行检查 | `src/minuteflow/guardrails/evidence.py` | 已按模式原创实现 |
| `references/openai-agents-python/examples/agent_patterns/llm_as_a_judge.py` | 独立评估者检查候选输出 | Verification Agent | 已采用独立验证思想和一次有限回退 |
| `references/superpowers/skills/verification-before-completion/SKILL.md` | 证据先于完成声明 | Evidence Grounding Skill | 采用原则 |
| `references/superpowers/skills/brainstorming/SKILL.md` | 识别范围、歧义和成功标准 | `docs/PROJECT.md` 与测试场景 | 采用需求分析原则 |
| `references/anthropic-skills/skills/skill-creator/SKILL.md` | Skill 单一职责、测试提示和迭代评估 | `skills/SKILLS.md`、`evals/TEST_SCENARIOS.md` | 采用结构与评估思想 |
| [OpenAI Agents SDK orchestration](https://openai.github.io/openai-agents-python/multi_agent/) | code orchestration、structured outputs 与 evaluator loop | `framework/DECISION.md`、`framework/PROFILE.md` | 选为未来 runtime Profile 的官方依据 |

## 未选用

- `references/mem0/`：MinuteFlow 不需要跨会议记忆，加入 Memory 会制造无必要复杂度。
- OpenAI Agents SDK 的 Handoff、多 Agent 并行、Session 与 MCP：本项目是短顺序流程，没有相应需求。
- 外部 SaaS Connector：输入是一份本地文本，任何外部连接都超出测试目标。
