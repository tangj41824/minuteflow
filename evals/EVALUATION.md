---
managed_by: agent-builder
update_mode: auto
version: 5
last_updated: 2026-08-05
project_id: minuteflow
evaluation_scope: framework-and-offline-implementation
status: offline-tests-passed
---

# MinuteFlow Implementation Evaluation

## 评估范围

本次同时评估框架一致性和独立 Python 实现。自动化测试全部使用 Scripted Agent Backend，不调用 OpenAI API；因此可以证明控制流、契约、Guardrail、Delivery 和 CLI 行为，但不能代替真实模型质量评测。

## 验收结果

| 验收标准 | 实现证据 | 结果 |
|---|---|---|
| MF-01 Agent 职责清晰 | Intake/Delivery 位于 `steps/`；Extraction/Verification 位于 `agents/`；Controller 位于 `orchestration.py` | 代码通过 |
| MF-02 每条结果有证据 | Pydantic EvidenceSpan、SDK Output Guardrail、Controller 二次检查及无效 `L99` 测试 | 代码通过 |
| MF-03 不编造负责人或日期 | Delivery 会删除证据中不存在的 owner/due_date，并自动生成澄清问题 | 代码通过 |
| MF-04 有限回退 | 自动化测试确认最多重新 Extraction/Verification 一次，`retry_count == 1` | 代码通过 |
| MF-05 三类场景 | clear、ambiguous、empty-result 和 empty-input 场景均已自动化 | 代码通过 |
| MF-06 最小复杂度 | 只有两个模型 Agent；没有 Memory、数据库、Connector、Handoff 或并行 Agent | 代码通过 |
| FW-01 框架选择有证据 | 实际使用 `openai-agents 0.19.4` 的 Runner、structured output、Guardrail 和可选 trace | 代码通过 |
| DIR-01 目录职责清晰 | 源码、测试、evals、设计文档和运行配置分区；根目录只保留标准入口与配置 | 代码通过 |
| SEP-01 Builder 与源码分离 | 业务代码位于 `minuteflow`，Agent Builder 只回写摘要 | 代码通过 |
| HND-01 独立实现可运行 | Python 3.11 虚拟环境安装成功；CLI help/version 和缺 Key 错误路径通过 | 代码通过 |
| IMPL-01 SDK 契约可执行 | 两个 Agent 均有 Pydantic output type 和 SDK output guardrail | 代码通过 |
| PRIV-01 默认隐私边界 | 离线测试不需 Key；Tracing 默认关闭；实时运行缺 Key 时发送前失败 | 代码通过 |

## 自动化验证结果

```text
pytest                         19 passed
ruff check src tests           All checks passed
ruff format --check src tests  26 files already formatted
pip check                      No broken requirements found
minuteflow --version           minuteflow 0.1.0
```

## 场景结果

### Clear

- 一个明确决定和两个明确行动通过。
- 缺少日期的 Leo 行动保留空值并生成澄清问题。
- 每个最终记录显示原始行号和原文。

### Ambiguous

- “maybe”“might”和未形成决定的表述被拒绝。
- Alex 不会因为发言而成为 owner。
- 正常输出空决定、空行动和澄清问题。

### Empty result

- 没有承诺时正常返回空列表和说明，不制造填充项。

### Safety and retry

- `L99` 等无效证据使流程关闭，不会进入 Verification。
- 证据中不存在的 owner 会被确定性移除。
- 可修正结果只重试一次。
- 空输入在调用 Agent 之前停止。

## 尚未验证

- 没有用户 API Key，因此没有运行真实 OpenAI 模型 smoke test，也没有产生模型费用。
- 不同语言、纪要长度和模型配置下的语义准确率仍需用代表性数据评测。
- 尚未部署 Web/API 服务；它们不属于 0.1.0 范围。

## 总体结论

- 框架状态：通过。
- 离线实现状态：通过。
- Live 模型质量状态：未验证，需用户主动配置 API Key 后单独测试。
