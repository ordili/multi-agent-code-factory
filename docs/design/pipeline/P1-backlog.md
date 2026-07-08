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
- [x] Live LLM（DeepSeek / Ollama）+ prompted JSON 路径
- [x] `spec.md` 渲染（`renderers/spec_md.py`）
- [x] `design.json` + `flow.mmd` 落盘
- [x] `run_meta.budget.used_llm_calls` + `llm_usage.json` + 用量日志（2026-07 补充）

---

## 1. 人读产物（评审 / HITL）

| 状态 | 项 | 落点 | 参考 |
|------|-----|------|------|
| [x] | **`design.md` 渲染** | `renderers/design_md.py`；`architect.py` 写入 | [artifact-templates/design.md](./artifact-templates/design.md) |
| [x] | **`review.md` 渲染** | `renderers/review_md.py`；`reviewer.py` 写入 | [artifact-templates/review.md](./artifact-templates/review.md) |
| [x] | `spec.md` 渲染 | `renderers/spec_md.py` | — |
| [x] | `flow.mmd` 写出 | `architect.py` | [artifact-templates/flow.md](./artifact-templates/flow.md) |

---

## 2. 校验规则（MVP 白名单之外）

> MVP 白名单见 [implementation-plan.md §3.1](./implementation-plan.md#31-mvp-规则白名单)。

### 2.1 Spec

| 状态 | 项 | 落点 |
|------|-----|------|
| [ ] | SPEC-101–114、201–202（可测性，多为 warn） | `validators/spec_rules.py` |
| [ ] | SPEC-301–308（`spec.md` 格式） | `validators/spec_md_rules.py` |

### 2.2 Design

| 状态 | 项 | 落点 |
|------|-----|------|
| [ ] | DES-012–033（域模型、错误码、接口、test_cases 等） | `validators/design_rules.py` |
| [ ] | DES-201–221（`design.md` / `flow.mmd` 格式） | `validators/design_md_rules.py`（新建） |

### 2.3 Mermaid

| 状态 | 项 | 落点 |
|------|-----|------|
| [ ] | DES-203 等 Mermaid 语法校验 | `validators/mermaid.py` |
| [~] | `validate_mermaid` Profile 开关 | 已有字段，默认 `false`；依赖上项 |

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
| [ ] | 非 Python 语言 **prompts** 补全 | go/java/rust/solidity | `profiles/*/prompts/` |

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
| [ ] | **`Profile.sandbox`**（隔离执行测试） | `profiles.md`、OpenHands 式 |
| [ ] | **`profiles/*/agents.yaml`**（CrewAI 风格 per-role） | `profiles.py` |
| [ ] | Gradle Windows `gradlew.bat` 归一 | `profiles.py`（P2 提及，可选） |

---

## 8. 预算与可观测性

| 状态 | 项 | 落点 |
|------|-----|------|
| [x] | `used_llm_calls` / `used_tokens` 记录 | `llm_runner.py`、`run_meta.json` |
| [x] | 每次 call 用量日志 + `llm_usage.json` | `agents/llm_usage.py` |
| [ ] | **`budget` 触顶熔断**（超 `FACTORY_MAX_TOKENS` fail） | `llm_runner._check_budget` |
| [ ] | LangSmith Trace 关联 `task_id` | 可选；`.env.example` 已有占位 |

---

## 9. P2 / V2（不在 P1，但 roadmap 相关）

| 项 | 说明 |
|----|------|
| `--parent-task-id` 增量 merge | [主线 §4.7](./multi-agent-pipeline-design.md) |
| `Profile.mcp_servers` / MCP Tool | [open-source-survey.md §C.5](./references/open-source-survey.md#c5-实现-backlog) |
| `solidity-hardhat` Profile | [profiles.md](./profiles.md) |
| **V2** `domains/*` 领域包 | [domains/README.md](../../../domains/README.md) |
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
- [ ] `design.md` 符合 [artifact-templates/design.md](./artifact-templates/design.md)

---

*最后更新：2026-07-08（与 calculator live run 现状对齐）*
