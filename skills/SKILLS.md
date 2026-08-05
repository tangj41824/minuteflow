---
managed_by: agent-builder
update_mode: auto
version: 2
last_updated: 2026-08-05
project_id: minuteflow
---

# MinuteFlow Skills

| Skill | 用途 | 使用者 | 输入 | 输出 | 来源 |
|---|---|---|---|---|---|
| Line Indexing | 为原文生成稳定行号且不改写内容 | Intake Agent | 原始文本 | `source_lines` | 项目原创，确定性规则 |
| Input Validation | 识别空输入、编码或结构警告 | Intake Agent | 原始文本 | 警告或可处理输入 | 项目原创，guardrail 思想参考 OpenAI Agents SDK |
| Decision/Action Extraction | 区分决定、承诺、建议与讨论 | Extraction Agent | 行号化文本 | 候选记录 | 项目原创，结构化输出模式参考 OpenAI Agents SDK |
| Uncertainty Normalization | 把缺失负责人、日期和模糊措辞显式化 | Extraction Agent | 候选记录 | 空字段与不确定标签 | 项目原创 |
| Evidence Grounding | 检查每条结论是否被指定行号直接支持 | Verification Agent | 原文与候选 | 通过或拒绝证据 | 参考 verification-before-completion 原则 |
| Ambiguity Detection | 识别建议、冲突和待确认信息 | Verification Agent | 原文与候选 | 待确认问题 | 项目原创 |
| Structured Report Rendering | 把通过记录转为稳定报告，不新增事实 | Delivery Agent | 验证结果 | `MeetingActionReport` | 项目原创 |

## Skill 设计规则

- 每项 Skill 只承担一种能力，不把整个 Workflow 包装成一个大 Skill。
- 确定性任务优先使用普通函数；只有语义分类和证据判断可能需要模型。
- Skills 已分别落位到 `steps/`、`agents/`、`guardrails/` 和 `renderers.py`；业务代码只存在于外部实现目录。
