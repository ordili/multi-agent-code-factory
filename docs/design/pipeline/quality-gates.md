# 产物校验与 HITL — PM / Architect

> **主线：** [multi-agent-pipeline-design.md §4.1.2](./multi-agent-pipeline-design.md#412-产物校验与-hitlpm--architect)  
> **原则：** **规则校验（程序）** 为主、**可选人工 HITL** 为辅；均在 **Developer 写代码之前** 拦截 PM / Architect 产物。  
> **实现：** `multi_agent_code_factory/validators/` · [`validation-report.md`](./artifact-schemas/validation-report.md)

---

## 0. 命名约定

**统一模式：** `{产物}_{动作}`。程序校验用 `_validate`，人工审批用 `_hitl`（与 `spec_hitl` 对称）。

| 图节点 | 模块 | 类型 | Run 产物 |
|--------|------|------|----------|
| **`spec_validate`** | `nodes/spec_validate.py` | 程序规则 | `spec_validation.json` |
| **`spec_hitl`** | `nodes/spec_hitl.py` | 人工 interrupt | `hitl.json`（`stage=spec`） |
| **`design_validate`** | `nodes/design_validate.py` | 程序规则 | `design_validation.json` |
| **`design_hitl`** | `nodes/design_hitl.py` | 人工 interrupt | `hitl.json`（`stage=design`） |
| **`deploy_hitl`** | `nodes/deploy_hitl.py` | 人工 interrupt | `hitl.json`（`stage=deploy`） |
| **`escalation_hitl`** | `nodes/escalation_hitl.py` | 人工 interrupt（loop 触顶） | `hitl.json`（`stage=escalation`） |

| Profile 配置块 | 说明 |
|----------------|------|
| **`validation`** | `spec` / `design` 规则开关（原 `gates`，已废弃） |
| **`hitl`** | deploy 阶段敏感路径 / flags（供 `deploy_hitl` 判定） |

| 其它 | 约定 |
|------|------|
| **`ValidationReport.target`** | `spec` \| `design`（校验对象；原字段名 `gate` 已废弃） |
| **`on_limit_exceeded`** | `fail` \| `escalation_hitl`（loop 触顶；`deploy_hitl` / `human_gate` 为旧别名，已废弃） |
| **Reviewer** | QA 后 LLM 审查（`reviewer`），**不是** HITL 节点 |

**五 Agent 命名：** 正文用 PM / Architect / Developer / QA / Reviewer；代码与路由用 `role_id` — 详见主线 [§3.1](./multi-agent-pipeline-design.md#31-角色命名约定)。

---

## 1. 在流水线中的位置

```text
PM → spec_validate → [spec_hitl?] → Architect → design_validate → [design_hitl?] → Developer → QA → Reviewer → [deploy_hitl?] → Deploy
```

| 节点 | 类型 | 失败 / 驳回 |
|------|------|-------------|
| **spec_validate** | 程序 | → **PM** |
| **spec_hitl** | 人工 | 驳回 → **PM** |
| **design_validate** | 程序 | → **Architect** |
| **design_hitl** | 人工 | 驳回 → **Architect** |
| **deploy_hitl** | 人工 | 部署 / 敏感变更（Reviewer 通过后） |

**可信度：** `TestReport` > `ValidationReport` > `HitlDecision` > `ReviewReport`（LLM）。

---

## 2. Profile 配置（`validation`）

```yaml
validation:
  spec:
    enabled: true
    block_on: error          # error | warn | never
    require_hitl: false
  design:
    enabled: true
    block_on: error
    require_hitl: false
    validate_mermaid: true
    require_hitl_if_flags: [touches_production]
```

| 字段 | 说明 |
|------|------|
| `enabled` | false 则跳过该 validate 节点（仍做 Pydantic 结构校验） |
| `block_on` | `error` 阻断；`warn` 只记录；`never` 仅落盘报告 |
| `require_hitl` | 规则通过后是否强制 `spec_hitl` / `design_hitl` |
| `require_hitl_if_flags` | 命中 `design.hitl_flags` 时强制 `design_hitl` |
| `validate_mermaid` | 是否解析 `flow.mmd` |

**生产级 Profile 示例（P1）：** 可设 `validation.spec.require_hitl: true`、`validation.design.require_hitl: true`，并配置 `hitl.sensitive_globs` / `hitl.flags` 触发 `deploy_hitl`。

---

## 3. spec_validate — 规则清单

实现：`multi_agent_code_factory/validators/spec_rules.py`。

### 3.1 结构与必填（error）

| rule_id | 检查 |
|---------|------|
| `SPEC-001` | `acceptance_criteria` 非空 |
| `SPEC-002` | AC `id` 唯一 |
| `SPEC-003` | `scope_in` 非空 |
| `SPEC-004` | `title`、`summary` 非空 |
| `SPEC-005` | `profile` 与 CLI 一致 |
| `SPEC-006` | `context.language` 与 Profile.`language` 一致 |
| `SPEC-007` | `context` 通过 `context_schema`（若配置） |
| `SPEC-008` | story / requirement / feature / metric 各类 `id` 无重复 |
| `SPEC-009` | `features` 非空 |
| `SPEC-010` | `features[].id` 唯一 |
| `SPEC-011` | `success_metrics` 非空 |
| `SPEC-012` | `success_metrics[].id` 唯一；`target` 非空 |
| `SPEC-013` | `operational_profile` 非空 |
| `SPEC-014` | `user_scale`、`high_concurrency`、`performance.tier` 必填 |
| `SPEC-015` | `consistency_profile` 非空 |
| `SPEC-016` | `consistency_model`、`delivery`、`multi_writer`、`idempotency_required` 必填 |

### 3.2 可测性与一致性

| rule_id | 严重度 | 检查 |
|---------|--------|------|
| `SPEC-101`–`105` | error/warn | `verifiable_by`、P0 覆盖、scope 互斥、constraints、`feature_id` 引用合法等 |
| `SPEC-106` | warn | 每个 P0 `features[]` 在 AC 或 KPI 中有可追溯覆盖 |
| `SPEC-107` | warn | `requirement_pool` 与 `features` 描述不得逐条重复（须更细或不同角度） |
| `SPEC-108` | warn | `high_concurrency=true` 时 `performance.tier` 不应为 `best_effort`（须 `interactive` 及以上或说明） |
| `SPEC-109` | warn | `performance.tier=custom` 时 `performance.notes` 非空（**文字**即可；具体数值在 design） |
| `SPEC-110` | warn | `consistency_model=eventual` 时 `notes` 宜含 **定性** 滞后预期（不写秒数；秒数在 design） |
| `SPEC-111` | error | `consistency_model=custom` 时 `notes` 非空 |
| `SPEC-112` | warn | `multi_writer=true` 时 `conflict_strategy` 不应为 `not_applicable` |
| `SPEC-113` | warn | `idempotency_required=true` 且 `delivery=at_least_once` 时，AC 或 KPI 宜覆盖重试/幂等（可追溯） |
| `SPEC-114` | warn | spec 阶段 `operational_profile` / `consistency_profile` 中 `latency`、`throughput`、`availability`、`staleness_bound`、`recovery` **宜为空**（数值归属 design） |
| `SPEC-201`–`202` | warn | 含 `automated_test` AC；`revision` 合法 |

### 3.3 spec.md 格式（P1，warn）

实现：`multi_agent_code_factory/validators/spec_md_rules.py`（读 run 目录 `spec.md`，对照 `spec.json`）。  
模板：[artifact-templates/spec.md](./artifact-templates/spec.md)。

| rule_id | 严重度 | 检查 |
|---------|--------|------|
| `SPEC-301` | warn | 须含 `## 概述` |
| `SPEC-302` | warn | 须含 `## 验收标准` |
| `SPEC-303` | warn | 须含 `## 范围` |
| `SPEC-304` | warn | MD 中出现的 `AC-*` id 与 `spec.json` 一致 |
| `SPEC-305` | warn | 文末元数据含 `task_profile`、`revision` |
| `SPEC-306` | warn | 须含 `## 成功指标` |
| `SPEC-307` | warn | 须含 `## 功能` |
| `SPEC-308` | warn | 须含 `## 稳定性、性能与数据一致性`（或等价含「数据一致性」子节） |

**失败：** `route_after_spec_validate` → **pm**；violations 注入 PM prompt。

---

## 4. design_validate — 规则清单

实现：`multi_agent_code_factory/validators/design_rules.py`。

### 4.1 JSON 结构（error / warn）

| rule_id 段 | 内容 |
|------------|------|
| `DES-001`–`007` | dev_tasks、file_plan、依赖无环、modules 等 |
| `DES-008` | `context_view`、`architecture.solution_strategy`、`non_goals` 非空 |
| `DES-009` | `traceability` 非空；P0 `FEAT` 在 `traceability` 或 `dev_tasks.covers` 可追溯 |
| `DES-010` | `cross_cutting` 非空（或 §6 其它字段齐全时可空对象） |
| `DES-011` | error | spec §8 非 trivial 时 `non_functional` 非空 |
| `DES-012` | `external_dependencies` 非空（无中间件时显式 `filesystem`/`none` 说明） |
| `DES-013` | `table_schemas` 非空，或 `data_model` + 字段级 `table_schemas.columns` |
| `DES-014` | `transaction_constraints` 非空（落实 spec `consistency_profile`） |
| `DES-015` | `error_catalog` 非空；至少 1 条可映射到 Flow 异常分支 |
| `DES-016` | `test_cases` 非空；每个 P0 AC 至少 1 条用例或 `covers` 追溯 |
| `DES-017` | `diagrams[]` 同时含 `kind=sequence` 与 `kind=flowchart` |
| `DES-018` | error | 每个 `table_schemas[].columns[]` 须显式 `nullable`（boolean）与非空 `description` |
| `DES-019` | error | `storage` 为关系型 DB 时：须含 `created_at`、`updated_at` 列；`indexes` 非空或 `notes` 说明仅 PK；`require_version` 为 true 时须含 `version` 列 |
| `DES-020` | warn | 每个 `indexes[]` 条目须含 `purpose`（索引注释） |
| `DES-021` | error | 每个 `error_catalog[].code` 至少 1 条 `test_cases[]` 且 `kind=negative` 且 `error_code` 匹配 |
| `DES-022` | warn | `test_cases[]` 须同时含 `kind=happy` 与 `kind=negative`；P0 FEAT/US 各有 happy 覆盖 |
| `DES-023` | error | `error_catalog[].code` 匹配 `^ERR-[A-Z][A-Z0-9_]{1,11}-\d{3}$` |
| `DES-024` | error | `test_cases[].id` 匹配 `^TC-(HAP|NEG|BND)-[A-Z][A-Z0-9_]{1,11}-\d{3}$` |
| `DES-025` | error | `test_cases[].error_code`（若有）须存在于 `error_catalog[].code` |
| `DES-026` | warn | `kind` 与 id 中段一致（如 `negative` ↔ `NEG`） |
| `DES-027` | error | 每个 `modules[]` 须含非空 `code_domain`，匹配 `^[A-Z][A-Z0-9_]{1,11}$`，且 **模块间不重复** |
| `DES-028` | error | 每个 `external_dependencies[]` 须含 `code_domain`（**`kind=none` 可省略**）；`kind` 为 `db`/`cache`/`mq`/`rpc`/`api`/`blockchain` 时 **不得** 与任一 `modules[].code_domain` 或其它非 `filesystem` 依赖重复；`kind=filesystem` 时须 **等于** 封装该 IO 的某模块 `code_domain` |
| `DES-029` | error | `error_catalog[].code` 的 `{域}` 段须存在于已注册域集合（`modules` + `external_dependencies` 的 `code_domain` 并集，**不含** `kind=none` 条目） |
| `DES-030` | error | `test_cases[].id` 的 `{域}` 段须存在于已注册域集合 |
| `DES-031` | warn | `kind=negative` 且同时填 `error_code` 时，`error_code` 与 `id` 的 `{域}` 宜一致（集成测包装上游码时须在 `notes` 说明） |
| `DES-032` | error | 每个 `modules[]` 须存在 `interfaces[]` 条目且 `module_ref`（或 `name`）匹配；**`code_domain=SYS` 的模块豁免** |
| `DES-033` | error | 每个 `interfaces[].operations[]` 非空；每条 `OperationSpec` 须含非空 `summary`，且 `inputs`/`outputs` 数组存在（可为空数组表示无参/无返回值） |
| `DES-034` | warn | `operations[].errors[]`（若有）须存在于 `error_catalog[].code` |
| `DES-101`–`104` | AC 追溯、scope_out、路径逃逸 |

### 4.2 design.md / flow.mmd 格式（P1）

模板：[artifact-templates/design.md](./artifact-templates/design.md)、[artifact-templates/flow.md](./artifact-templates/flow.md)。

| rule_id | 严重度 | 检查 |
|---------|--------|------|
| `DES-201` | warn | 须含 §1–§6 标题（Context…Cross-cutting；Google Design Doc 核心） |
| `DES-202` | warn | 须含附录 A–C |
| `DES-203` | error* | `flow.mmd` 可解析 |
| `DES-204` | warn | sequence participant 与 `modules` / `interfaces` 一致 |
| `DES-205` | warn | §8 Testing Plan 或 `test_strategy.approach` 非空 |
| `DES-206` | warn | §4 Design 须含 Flow 子节或引用 `flow.mmd` |
| `DES-207` | warn | 须含附录 E |
| `DES-208` | warn | Profile 含 deploy 时须含 §9 Rollout & Deployment |
| `DES-209` | warn | 须含 §3 Non-Goals |
| `DES-210` | warn | 须含 §11 Open Questions |
| `DES-211` | warn | Profile 为长运行服务时 §10 Monitoring 非 N/A |
| `DES-212` | warn | 须含 `### 4.3 External Dependencies` |
| `DES-220` | warn | 须含 `### 4.2 Components` 且表格含 `code_domain` 列 |
| `DES-221` | warn | 须含 `### 4.4 APIs` 且各模块 API 表含「入参」「出参」列（或等价结构化描述） |
| `DES-213` | warn | 须含 `### 4.5 Data Model & Table Schema` |
| `DES-214` | error* | `diagrams[]` 须同时登记 sequence 与 flowchart；`flow.mmd` 内须可识别两类图 |
| `DES-215` | warn | 须含 `## 附录 D. 测试用例设计` 或 `test_cases` 非空 |
| `DES-216` | warn | 须含 `### 6.1` 事务/一致性 与 `### 6.2` 错误码 |
| `DES-217` | warn | 须含 `### 4.6 Flow` 且引用 `flow.mmd` |
| `DES-218` | warn | §4.5 表格须含「可空」「注释」列 |
| `DES-219` | warn | 附录 D 须含「类型」列（happy/negative/boundary） |

\* `DES-203` 在 `validation.design.validate_mermaid: false` 时降为 warn 或跳过。

### 4.4 HITL 标志

| rule_id | 检查 |
|---------|------|
| `DES-301` | `hitl_flags` 命中 → 路由标记 `require_hitl` → **design_hitl** |

---

## 5. HITL 节点（spec_hitl / design_hitl / deploy_hitl / escalation_hitl）

LangGraph **`interrupt_before`**；[`HitlDecision.stage`](./artifact-schemas/hitl.md)：

| `stage` | 节点 | 审批人阅读 | 驳回 / 终止 |
|---------|------|------------|-------------|
| `spec` | spec_hitl | `spec.md`、`spec_validation.json` | → PM |
| `design` | design_hitl | `design.md`、`flow.mmd`、`design_validation.json` | → Architect |
| `deploy` | deploy_hitl | `review.md`、diff、敏感变更 | 续跑 → Developer；终止 → `run_meta.status=failed` |
| `escalation` | escalation_hitl | run 摘要、回路计数、最近失败产物 | → `run_meta.status=failed` |

### 5.1 escalation_hitl（loop 触顶，P1）

**配置：** `on_limit_exceeded: escalation_hitl`（默认 `fail`，MVP 可不实现节点）。

| 项 | 约定 |
|----|------|
| **触发** | 任一回路的 `*_revision_count` 或 `impl_retry_count` 达 `loop_limits` 上限 |
| **写入** | `hitl.json`（`stage=escalation`）；`reason` 示例：`loop_limit:impl_retry`、`loop_limit:spec_revision` |
| **继续** | `approved=true` 且人工在 CLI/UI 指定重置计数 → 从主线 [§4.3 再入点](./multi-agent-pipeline-design.md#再入规则升环--validate-失败后) 续跑 |
| **与 deploy_hitl** | **不可互换**；deploy 仅 Reviewer 成功路径 + Profile.`hitl` 敏感规则 |

---

## 6. 与 Reviewer Agent 的分工

| | spec_validate / design_validate | Reviewer（LLM） |
|--|--------------------------------|-----------------|
| **时机** | Developer 前 | QA 后 |
| **对象** | 文档规则 | 代码 + 测试 + AC |
| **确定性** | 是 | 否 |

---

## 7. 实现落点

```text
multi_agent_code_factory/
├── validators/          # spec_rules.py, design_rules.py, mermaid.py
├── nodes/
│   ├── spec_validate.py
│   ├── design_validate.py
│   ├── spec_hitl.py
│   ├── design_hitl.py
│   ├── deploy_hitl.py
│   └── escalation_hitl.py   # P1；MVP 默认 on_limit_exceeded=fail
└── schemas/validation_report.py
```

---

## 8. 路由伪代码

**程序真源：** [multi-agent-pipeline-design.md §4.3](./multi-agent-pipeline-design.md#路由伪代码程序真源)（`graph_routing.py`）。本节不再重复；实现须与主线伪代码一致，含 `loop_limits` 触顶判断与 `route_after_review` 对 `approved` 的守卫。
