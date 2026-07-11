# P1 Backlog — 待办与验收跟踪

## 依赖上游文档（只读）

维护 backlog 时 **以本表及正文勾选清单为准**；冲突时以总设计与实现计划为准。`quality-gates/` 规则细目为**下游**，正文按需查阅。


| 分类       | 上游文档                                                                          | 定位                    |
| -------- | ----------------------------------------------------------------------------- | --------------------- |
| **总设计**  | [multi-agent-pipeline-design.md](./multi-agent-pipeline-design.md) | 系统的总体设计书 |
| **实现计划** | [implementation-plan.md](./implementation-plan.md)                            | 阶段、PR 拆分与验收对照    |


---

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
| [quality-gates/](./quality-gates/README.md) | 校验 rule_id 全表 |

**图例：** `[x]` 已完成 · `[ ]` 待做 · `[~]` 部分完成（占位或 MVP 简化版）

---

## 0. MVP 主路径（参考，非 P1）

以下已在 Python live 路径验证（如 `calculator` task），**不计入 P1**，仅作基线：

- [x] 五 Agent + validate + QA + Reviewer 图跑通
- [x] `prd_validate` / `design_validate` MVP 白名单规则
- [x] `run_tests` + `junit_xml` Parser
- [x] Live LLM（DeepSeek / Ollama `prompted_json`；OpenAI / Anthropic `native_structured`）
- [x] LLM 调用分层（`agents/llm/`：pipeline、strategies、retry、budget、usage）
- [x] `prd.md` 渲染（`renderers/prd_md.py`）
- [x] `design.json` + `flow.mmd` 落盘
- [x] `run_meta.budget.used_llm_calls` + `llm_usage.json` + 用量日志（2026-07 补充）

---

## 1. 人读产物（评审 / HITL）

| 状态 | 项 | 落点 | 参考 |
|------|-----|------|------|
| [x] | **`design.md` 渲染** | `renderers/design_md.py`；`architect.py` 写入 | [artifact-templates/design-spec.md](./artifact-templates/design-spec.md)（定稿 §1–§6 + 附录 A–D） |
| [x] | **`prd.md` 渲染** | `renderers/prd_md.py` | [artifact-templates/prd-spec.md](./artifact-templates/prd-spec.md)（中文 §1–§12） |
| [x] | `flow.mmd` / 多 `*.mmd` 写出 | `architect.py`（`mmd_files[]`） | [artifact-templates/flow-spec.md](./artifact-templates/flow-spec.md) |

---

## 2. 校验规则（MVP 白名单之外）

> MVP 白名单见 [implementation-plan.md §3.1](./implementation-plan.md#31-mvp-规则白名单)。

### 2.1 Spec

| 状态 | 项 | 落点 |
|------|-----|------|
| [x] | PRD-101–114、201–202、017（可测性 / storage，多为 warn） | `validators/prd_rules.py` + `spec_rules_extended.py` |
| [x] | PRD-301–316（`prd.md` 格式） | `validators/prd_md_rules.py` |

### 2.2 Design

| 状态 | 项 | 落点 |
|------|-----|------|
| [x] | DES-012–036（域模型、错误码、接口、交付 intent 等） | `validators/design_rules.py` + `design_rules_extended.py` |
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
| [~] | `prd_hitl` 节点 | `nodes/prd_hitl.py` | 存在；MVP **自动 approved**，无 interrupt |
| [~] | `design_hitl` 节点 | `nodes/design_hitl.py` | 同上 |
| [ ] | LangGraph **强制 interrupt** + CLI/UI **resume** | `graph.py`、CLI | 生产级 `require_hitl: true` |
| [~] | `escalation_hitl` | `nodes/escalation_hitl.py` | 占位 → fail |
| [ ] | `on_limit_exceeded=escalation_hitl` 完整流程 | `config.py`、`graph_routing.py` | |
| [ ] | `max_hitl_rounds`  enforcement | `autonomy_policy.yaml`、`run_meta` | 默认 5 |
| [ ] | `hitl_history[]` / `hitl_log.jsonl` | `run_meta`、`write_artifact.py` | 多轮 HITL 审计 |
| [ ] | 生产 Profile 示例（`require_hitl: true`） | `profiles/*.yaml` | 见 [quality-gates/README.md §2](./quality-gates/README.md) |

---

## 4. 断点续跑 / 升环审计

| 状态 | 项 | 落点 |
|------|-----|------|
| [x] | 产物续跑 `continue --task-id` | [artifact-continue-design.md](./artifact-continue-design.md)、`__main__.py`、`graph/runner.py` |
| [x] | `artifact_loader` + `infer_reentry_node` | `artifact_loader.py`、`checkpoint.py` |
| [x] | `prepare_continue`（budget / 触顶 loop 重置） | `tools/run_artifacts/meta.py` |
| [x] | LangGraph checkpointer 集成（`continue`） | `checkpoint.py`、`graph/graph_builder.py` |
| [~] | `checkpoint.py` `resume` | 占位 `NotImplementedError` |
| [ ] | CLI `resume --task-id` | `__main__.py` |
| [ ] | `run_meta.checkpoint_id` 写入 | `write_artifact.py` |
| [x] | `stale_artifacts[]`（升环后作废路径） | `tools/run_artifacts/meta.py`、`artifact_loader.py` |

---

## 5. 多语言 QA / Parser

| 状态 | 项 | Profile | 落点 |
|------|-----|---------|------|
| [x] | `junit_xml` | python, java | `tools/test_parsers/junit_xml.py` |
| [x] | `exit_code_only` | — | `tools/test_parsers/exit_code_only.py` |
| [x] | **`go_json`** | go | `tools/test_parsers/go_json.py` |
| [x] | **`cargo_json`** | rust | `tools/test_parsers/cargo_json.py` |
| [x] | **`forge_json`** | solidity | `tools/test_parsers/forge_json.py` |
| [ ] | Go / Rust / Solidity **live e2e** 各一例 | — | `tests/integration/` |
| [x] | 多语言 **Developer prompt** + **style snippet** | go/java/rust/solidity/python | `profiles/*/prompts/developer.txt`、`{language}-style-snippet.txt` |
| [x] | **Developer 重试上下文**（RetryBundle 瘦身 + `failure_contexts` + patch-only） | 全部 V1 Profile | [developer-retry-context-spec.md](./developer-retry-context-spec.md) · `retry_context.py` · `prompt_context.py` |
| [ ] | **Developer 分步实现**（`dev_tasks` task-batch） | 大项目 / 多 task design | [developer-task-batch-spec.md](./developer-task-batch-spec.md) |

---

## 6. QA / Developer 增强

| 状态 | 项 | 落点 |
|------|-----|------|
| [x] | `tests_missing` 检测（对照 `test_dir_glob`） | `tools/tests_missing.py` → `run_tests.py` / `agents/qa.py` |
| [x] | `auto_generate_tests`（缺测时） | `passed=false` + Developer context 注入 `tests_missing` / `auto_generate_tests` |
| [x] | Reviewer **`git_diff` Tool** | `tools/git_diff.py` → `prompt_context.py` / `tools/registry.py` |

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
| [x] | LangSmith Trace 关联 `task_id` | `observability/langsmith.py` → `graph/runner.py`（`run_name` + metadata/tags） |

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

1. **`design.md` 渲染** — 开发评审缺口（与 `prd.md` 对称）
2. **Mermaid + design 格式校验** — 设计质量门槛
3. **多语言 Parser + e2e** — 若下一目标是 Go/Rust
4. **HITL interrupt + checkpoint/resume** — 若下一目标是生产部署
5. **sandbox + git_diff** — 若下一目标是安全/审查增强

---

## 11. 验收对照（§10 中仍为 P1 的项）

复制自 [multi-agent-pipeline-design.md §10](./multi-agent-pipeline-design.md#10-验收)：

- [ ] `prd_hitl` / `design_hitl` interrupt 可暂停与恢复
- [x] `docs/runs/<task_id>/` 含 **`design.md`**
- [x] `go_json` Parser + Profile 注册（单元测试；live e2e 待补）
- [x] `cargo_json` / `forge_json` Parser（单元测试 + Profile 注册）
- [ ] Rust / Solidity **live e2e** 各一例
- [ ] `resume --task-id` 从 checkpoint 续跑
- [x] `design.md` 符合 [artifact-templates/design-spec.md](./artifact-templates/design-spec.md)
- [x] `prd.md` 符合 [artifact-templates/prd-spec.md](./artifact-templates/prd-spec.md)

---

*最后更新：2026-07-11（Developer 重试上下文 R0–R2 已实现；`go_json` Parser 落地）*
