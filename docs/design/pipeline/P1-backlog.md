# P1 Backlog — 待办与验收跟踪

> **用途：** 将分散在各设计 Spec 中的 **P1（及关联 P2）** 项汇总为一份可勾选清单。  
> **权威来源：** 冲突时以 [multi-agent-pipeline-design.md](./multi-agent-pipeline-design.md) §1.2、§10 与 [implementation-plan.md](./implementation-plan.md) 为准。  
> **维护：** 完成某项后在本文件勾选，并在 PR 中引用对应 rule_id / 模块路径。

**相关文档：**

| 文档 | 内容 |
|------|------|
| [implementation-plan.md](./implementation-plan.md) §14 | V1 明确不做（= 本清单主体） |
| [multi-agent-pipeline-design.md](./multi-agent-pipeline-design.md) §10 | 发布验收 checklist |
| [metagpt.md](./references/metagpt.md) §B.3 | MetaGPT 机制 backlog |
| [open-source-survey.md](./references/open-source-survey.md) §C.5 | 沙箱 / diff / MCP backlog |
| [quality-gates.md](./quality-gates.md) | 校验 rule_id 全表 |

**图例：** `[x]` 已完成 · `[ ]` 待做 · `[~]` 部分完成（占位或 MVP 简化版）

---

## 0. MVP 主路径（参考，非 P1）

以下已在 Python live 路径验证（如 `calculator` task），**不计入 P1**，仅作基线：

- [x] 五 Agent + validate + QA + Reviewer 图跑通
- [x] `spec_validate` / `design_validate` MVP 白名单规则
- [x] `run_tests` + `junit_xml` Parser
- [x] Live LLM（DeepSeek / Ollama `prompted_json`；OpenAI / Anthropic `native_structured`）
- [x] LLM 调用分层（`agents/llm/`：pipeline、strategies、retry、budget、usage）
- [x] `spec.md` 渲染（`renderers/spec_md.py`）
- [x] `design.json` + `flow.mmd` 落盘
- [x] `run_meta.budget.used_llm_calls` + `llm_usage.json` + 用量日志（2026-07 补充）

---

## 1. 人读产物（评审 / HITL）

| 状态 | 项 | 落点 | 参考 |
|------|-----|------|------|
| [x] | **`design.md` 渲染** | `renderers/design_md.py`；`architect.py` 写入 | [artifact-templates/design-spec.md](./artifact-templates/design-spec.md)（中文 §1–§10） |
| [x] | **`spec.md` 渲染** | `renderers/spec_md.py` | [artifact-templates/prd-spec.md](./artifact-templates/prd-spec.md)（中文 §1–§12） |
| [x] | `flow.mmd` / 多 `*.mmd` 写出 | `architect.py`（`mmd_files[]`） | [artifact-templates/flow-spec.md](./artifact-templates/flow-spec.md) |

---

## 2. 校验规则（MVP 白名单之外）

> MVP 白名单见 [implementation-plan.md §3.1](./implementation-plan.md#31-mvp-规则白名单)。

### 2.1 Spec

| 状态 | 项 | 落点 |
|------|-----|------|
| [x] | SPEC-101–114、201–202（可测性，多为 warn） | `validators/spec_rules.py` + `spec_rules_extended.py` |
| [x] | SPEC-301–313（`spec.md` 格式） | `validators/spec_md_rules.py` |

### 2.2 Design

| 状态 | 项 | 落点 |
|------|-----|------|
| [x] | DES-012–034（域模型、错误码、接口、test_cases 等） | `validators/design_rules.py` + `design_rules_extended.py` |
| [x] | DES-201–223（`design.md` / `*.mmd` 格式） | `validators/design_md_rules.py` |

### 2.3 Mermaid

| 状态 | 项 | 落点 |
|------|-----|------|
| [x] | DES-203/214 等 Mermaid 语法校验 | `validators/mermaid.py` |
| [x] | `validate_mermaid` Profile 开关 | `design_validate.py` 已接入 |

---

## 3. HITL / 人工审批

| 状态 | 项 | 落点 | 说明 |
|------|-----|------|------|
| [~] | `spec_hitl` 节点 | `nodes/spec_hitl.py` | 存在；MVP **自动 approved**，无 interrupt |
| [~] | `design_hitl` 节点 | `nodes/design_hitl.py` | 同上 |
| [ ] | LangGraph **强制 interrupt** + CLI/UI **resume** | `graph.py`、CLI | 生产级 `require_hitl: true` |
| [~] | `escalation_hitl` | `nodes/escalation_hitl.py` | 占位 → fail |
| [ ] | `on_limit_exceeded=escalation_hitl` 完整流程 | `config.py`、`graph_routing.py` | |
| [ ] | `max_hitl_rounds`  enforcement | `autonomy_policy.yaml`、`run_meta` | 默认 5 |
| [ ] | `hitl_history[]` / `hitl_log.jsonl` | `run_meta`、`write_artifact.py` | 多轮 HITL 审计 |
| [ ] | 生产 Profile 示例（`require_hitl: true`） | `profiles/*.yaml` | 见 [quality-gates.md §2](./quality-gates.md) |

---

## 4. 断点续跑 / 升环审计

| 状态 | 项 | 落点 |
|------|-----|------|
| [~] | `checkpoint.py` | 占位 `NotImplementedError` |
| [ ] | LangGraph checkpointer 集成 | `checkpoint.py`、`graph.py` |
| [ ] | CLI `resume --task-id` | `__main__.py` |
| [ ] | `run_meta.checkpoint_id` 写入 | `write_artifact.py` |
| [ ] | `stale_artifacts[]`（升环后作废路径） | `write_artifact.py`、`graph_routing.py` |

---

## 5. 多语言 QA / Parser

| 状态 | 项 | Profile | 落点 |
|------|-----|---------|------|
| [x] | `junit_xml` | python, java | `tools/test_parsers/junit_xml.py` |
| [x] | `exit_code_only` | — | `tools/test_parsers/exit_code_only.py` |
| [ ] | **`go_json`** | go | `tools/test_parsers/go_json.py` |
| [ ] | **`cargo_json`** | rust | `tools/test_parsers/cargo_json.py` |
| [ ] | **`forge_json`** | solidity | `tools/test_parsers/forge_json.py` |
| [ ] | Go / Rust / Solidity **live e2e** 各一例 | — | `tests/integration/` |
| [x] | 多语言 **Developer prompt** + **style snippet** | go/java/rust/solidity/python | `profiles/*/prompts/developer.txt`、`{language}-style-snippet.txt` |
| [x] | **共享** PM / Architect / Reviewer prompt（语言无关） | 全部 V1 Profile | `profiles/_shared/prompts/`；`agents/llm/prompt/loader.py` |

---

## 6. QA / Developer 增强

| 状态 | 项 | 落点 |
|------|-----|------|
| [ ] | `tests_missing` 检测（对照 `test_dir_glob`） | `agents/qa.py` |
| [ ] | `auto_generate_tests`（缺测时） | Developer / QA 协作 |
| [ ] | Reviewer **`git_diff` Tool** | `tools/`、[open-source-survey.md](./references/open-source-survey.md) |

---

## 7. Profile / 运行环境

| 状态 | 项 | 落点 |
|------|-----|------|
| [x] | 多语言 **style snippet** 解析 | `agents/llm/prompt/style_snippet.py` |
| [ ] | **`Profile.sandbox`**（隔离执行测试） | `profiles.md`、OpenHands 式 |
| [ ] | **`profiles/*/agents.yaml`**（CrewAI 风格 per-role） | `profiles.py` |
| [ ] | Gradle Windows `gradlew.bat` 归一 | `profiles.py`（P2 提及，可选） |

---

## 8. 预算与可观测性

| 状态 | 项 | 落点 |
|------|-----|------|
| [x] | `used_llm_calls` / `used_tokens` 记录 | `agents/llm/usage/recorder.py`、`run_meta.json` |
| [x] | 每次 call 用量日志 + `llm_usage.json` | `agents/llm/usage/` |
| [x] | **`budget` 触顶熔断**（超 `FACTORY_MAX_TOKENS` / call 上限 fail） | `agents/llm/budget/guard.py` → `LlmBudgetExceededError` |
| [ ] | LangSmith Trace 关联 `task_id` | 可选；`.env.example` 已有占位 |

---

## 9. P2 / V2（不在 P1，但 roadmap 相关）

| 项 | 说明 |
|----|------|
| `--parent-task-id` 增量 merge | [主线 §4.7](./multi-agent-pipeline-design.md) |
| `Profile.mcp_servers` / MCP Tool | [open-source-survey.md §C.5](./references/open-source-survey.md#c5-实现-backlog) |
| `solidity-hardhat` Profile | [profiles.md](./profiles.md) |
| **V2** `domains/*` 领域包 | [domains/README.md](../../../domains/README.md) — **子任务清单见该文档** |
| LLM 固定 system 前缀 **Prompt Cache**（省 API 费用） | 暂缓；后期讨论 |
| AFlow 式工作流调参 | P3 |

---

## 10. 建议实施顺序（团队可调整）

1. **`design.md` 渲染** — 开发评审缺口（与 `spec.md` 对称）
2. **Mermaid + design 格式校验** — 设计质量门槛
3. **多语言 Parser + e2e** — 若下一目标是 Go/Rust
4. **HITL interrupt + checkpoint/resume** — 若下一目标是生产部署
5. **sandbox + git_diff** — 若下一目标是安全/审查增强

---

## 11. 验收对照（§10 中仍为 P1 的项）

复制自 [multi-agent-pipeline-design.md §10](./multi-agent-pipeline-design.md#10-验收)：

- [ ] `spec_hitl` / `design_hitl` interrupt 可暂停与恢复
- [x] `docs/runs/<task_id>/` 含 **`design.md`**
- [ ] `go_json` / `cargo_json` / `forge_json` Parser + Profile 各跑通一例
- [ ] `resume --task-id` 从 checkpoint 续跑
- [ ] `design.md` 符合 [artifact-templates/design-spec.md](./artifact-templates/design-spec.md)

---

*最后更新：2026-07-08（多语言 profile prompts、LLM 分层、共享角色 prompt、budget 熔断已勾选）*
