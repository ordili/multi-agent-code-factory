# prd_validate — 规则清单

## 依赖上游文档（只读）

审查 / 修订本文时 **仅以本表及正文规则表为准**；不引用 `validators/` 等下游实现。


| 分类        | 上游文档                                                                          | 定位                              |
| --------- | ----------------------------------------------------------------------------- | ------------------------------- |
| **总设计**   | [multi-agent-pipeline-design.md](../multi-agent-pipeline-design.md) | 系统的总体设计书 |
| **JSON 契约** | [artifact-schemas/prd-spec.md](../artifact-schemas/prd-spec.md)             | Run `prd.json` 字段与类型            |
| **人读模板**  | [artifact-templates/prd-spec.md](../artifact-templates/prd-spec.md)         | Run `prd.md` 章节                |
| **校验产出**  | [validation-report-spec.md](../artifact-schemas/validation-report-spec.md)  | `prd_validation.json` 与 `passed` |
| **运行配置**  | [README.md](./README.md) · [profiles.md](../profiles.md)                    | `validation.prd.*` 开关语义（详见 README §2） |


> **下游（不在此表）：** [design-validate.md](./design-validate.md) 只读引用本文 §prd→design 传导。


---

> **索引：** [quality-gates/README.md](./README.md)  
> **实现：** `multi_agent_code_factory/validators/prd_rules.py` · `prd_md_rules.py`  
> **JSON 契约：** [artifact-schemas/prd-spec.md](../artifact-schemas/prd-spec.md)  
> **人读模板：** [artifact-templates/prd-spec.md](../artifact-templates/prd-spec.md) → Run `prd.md`

**rule_id 合计：** **49** 条（§3.1 结构 **16** · §3.2 可测性 **17** · §3.3 `prd.md` 格式 **16**）。

> **PRD 通过 ≠ design 通过。** PRD 环只校验 [prd-spec.md](../artifact-schemas/prd-spec.md)；Architect 还须通过 [design-validate.md](./design-validate.md)（**57** 条 `DES-*`）。
> **必检** = 是否执行该 rule；**触发条件** = 何时执行或何时要求字段非空（与 [design-validate](./design-validate.md) 各 rule 的「触发条件」列一致）。

### prd → design 传导（只读）

Run `prd.md` 章节写法见 [artifact-templates/prd-spec.md](../artifact-templates/prd-spec.md)。

| PRD 信号 | 建议写法 | 触发的 design 义务 |
|-----------|----------|-------------------|
| `context.storage` 为持久化（`local_file` / `database` 等） | **须显式声明**介质 | `DES-013` 非空（`table_schemas` / `data_model`）；`DES-017` 要求 `diagrams[]` 同时含 `sequence` + `flowchart`（与是否写 §4.7 无关） |
| `context.storage` ∈ `none`/`memory`/`stateless`，且 `consistency_model=local_only`，且 `multi_writer=false` | 无持久化 CLI 定稿写法 | `table_schemas` / `transaction_constraints` / `diagrams` 可为 `[]`；仍须 `external_dependencies`（`kind=none`）等 |
| `consistency_profile.multi_writer=true` 或跨存储/多写 | 多写场景 | `DES-014` 非空 |
| `operational_profile` 含性能/可用性量化要求 | spec §9 非 trivial 占位 | `DES-011` |
| `acceptance_criteria` + `PRD-201` | 宜含 `automated_test` | `DES-016` / `DES-101` 覆盖 AC |
| design `modules` ≥2 **或** `external_dependencies` 含 `kind≠none` | 多模块 / 有外部依赖 | `DES-223`（warn §4.2 架构图 + `kind=context`） |
| design 已登记任一条 `diagrams[]`（含仅 `context`） | 宜与 Run `*.mmd` 一致 | `DES-017` / `DES-214`（须补全 `sequence` + `flowchart`） |

> **`storage` 省略：** 文档定稿要求 PM **不可省略**；由 **PRD-017** 门禁。  
> **与 design schema 对齐：** [design-spec 是否必填](../artifact-schemas/design-spec.md#字段) 中 `summary`、`design_goals`、`file_plan`、`architecture.code_delta` 标 **是**，但 JSON 层 **无** 对等 `DES-*` non-empty — 见 [design-validate §JSON 契约 vs 规则](./design-validate.md#json-契约-vs-规则与-schema是否必填对齐)。

---

## 3.1 结构与必填

本节 `severity` 均为 **error**。

| rule_id | 严重度 | 必检 | 触发条件 | 字段 | 判定 |
|---------|--------|------|----------|------|------|
| `PRD-001` | error | 是 | — | `acceptance_criteria` | 非空 |
| `PRD-002` | error | 是 | — | `acceptance_criteria[].id` | 唯一 |
| `PRD-003` | error | 是 | — | `scope_in` | 非空 |
| `PRD-004` | error | 是 | — | `title`、`summary` | 非空 |
| `PRD-005` | error | 是 | — | `profile` | 与 CLI Profile 一致 |
| `PRD-006` | error | 条件 | Profile 配置 `language` | `context.language` | 与 Profile.`language` 一致 |
| `PRD-007` | error | 条件 | Profile 配置 `context_schema` | `context` | 通过 `context_schema`（const / enum） |
| `PRD-008` | error | 是 | — | `user_stories[].id` / `requirement_pool[].id` / `features[].id` / `success_metrics[].id` | 各类内无重复 |
| `PRD-009` | error | 是 | — | `features` | 非空 |
| `PRD-010` | error | 是 | — | `features[].id` | 唯一 |
| `PRD-012` | error | 条件 | `success_metrics` 非空 | `success_metrics[].id`、`success_metrics[].target` | id 唯一；`target` 非空 |
| `PRD-013` | error | 是 | — | `operational_profile` | 对象须存在 |
| `PRD-014` | error | 是 | — | `operational_profile.user_scale`、`high_concurrency`、`performance.tier` | 必填 |
| `PRD-015` | error | 是 | — | `consistency_profile` | 对象须存在 |
| `PRD-016` | error | 是 | — | `consistency_profile.consistency_model`、`delivery`、`multi_writer`、`idempotency_required` | 必填 |
| `PRD-017` | error | 是 | — | `context.storage` | 非空、显式声明 |

> **必检：** **是** = 每次 `prd_validate` 均执行；**条件** = 仅当触发条件成立时执行。  
> **字段** 列与 [prd-spec.md](../artifact-schemas/prd-spec.md) JSON 契约一致（英文键名）。  
> **`success_metrics`（非 rule_id）：** 可选；JSON 可为 `[]`，无 empty 门禁。

## 3.2 可测性与一致性

| rule_id | 严重度 | 必检 | 触发条件 | 字段 | 判定 |
|---------|--------|------|----------|------|------|
| `PRD-101` | error | 是 | — | `acceptance_criteria[].description` | 非空 |
| `PRD-102` | warn | 是 | — | `acceptance_criteria[].verifiable_by` | P0 用户故事须在 AC 或 manual KPI 中可追溯 |
| `PRD-103` | warn | 是 | — | `scope_out` | 与 `scope_in` 互斥 |
| `PRD-104` | warn | 条件 | `constraints` 非空 | `constraints[]` | 条目非空 |
| `PRD-105` | error | 是 | — | `requirement_pool[].feature_id` | 引用合法 `features[].id` |
| `PRD-106` | warn | 是 | — | `features[]`（P0） | 在 AC 或 KPI 中可追溯 |
| `PRD-107` | warn | 是 | — | `requirement_pool[]`、`features[]` | 描述不得逐条重复 |
| `PRD-108` | warn | 条件 | `high_concurrency=true` | `operational_profile.performance.tier` | 不应为 `best_effort` |
| `PRD-109` | warn | 条件 | `performance.tier=custom` | `operational_profile.performance.notes` | 非空 |
| `PRD-110` | warn | 条件 | `consistency_model=eventual` | `consistency_profile.notes` | 宜含定性滞后预期 |
| `PRD-111` | error | 条件 | `consistency_model=custom` | `consistency_profile.notes` | 非空 |
| `PRD-112` | warn | 条件 | `multi_writer=true` | `consistency_profile.conflict_strategy` | 不应为 `not_applicable` |
| `PRD-113` | warn | 条件 | `idempotency_required=true` 且 `delivery=at_least_once` | `acceptance_criteria` / `success_metrics` | 宜覆盖重试/幂等 |
| `PRD-114` | warn | 是 | — | `operational_profile`、`consistency_profile` 数值子字段 | `latency` 等宜为空（数值归属 design） |
| `PRD-118` | warn | 条件 | `context.glossary` 非空 | `context.glossary[]` | 每项 `term`、`definition` 非空 |
| `PRD-201` | warn | 是 | — | `acceptance_criteria[].verifiable_by` | 宜含 `automated_test`（→ `DES-016`） |
| `PRD-202` | warn | 是 | — | `revision` | ≥ 1 |

## 3.3 Run `prd.md` 格式（P1，warn）

本节 `severity` 均为 **warn**。

校验 Run 目录 **`prd.md`**（非规范文件名 `prd-spec.md`）。章节模板见 [artifact-templates/prd-spec.md](../artifact-templates/prd-spec.md)。

实现：`validators/prd_md_rules.py`（读 run 目录 `prd.md`，对照 `prd.json`）。

| rule_id | 严重度 | 必检 | 触发条件 | 检查对象 | 判定 |
|---------|--------|------|----------|----------|------|
| `PRD-301` | warn | 是 | — | `prd.md` | 须含 `## 概述` |
| `PRD-302` | warn | 是 | — | `prd.md` | 须含 `## 验收标准` |
| `PRD-303` | warn | 是 | — | `prd.md` | 须含 `## 范围` |
| `PRD-304` | warn | 是 | — | `prd.md` 正文 | 出现的 `AC-*` id 与 `prd.json` 一致 |
| `PRD-305` | warn | 是 | — | `prd.md` 文末元数据 | 含 `task_profile`、`revision` |
| `PRD-306` | warn | 是 | — | `prd.md` | 须含 `## 业务指标`（无 KPI 时正文写「无」） |
| `PRD-307` | warn | 是 | — | `prd.md` | 须含 `## 功能` |
| `PRD-308` | warn | 是 | — | `prd.md` | 须含 `## 非功能性需求` |
| `PRD-309` | warn | 是 | — | `prd.md` | 须含 `## 术语与领域概念` |
| `PRD-310` | warn | 是 | — | `prd.md` | 须含 `## 背景与上下文` |
| `PRD-311` | warn | 是 | — | `prd.md` | 须含 `## 用户故事` |
| `PRD-312` | warn | 是 | — | `prd.md` | 须含 `## 需求池` |
| `PRD-313` | warn | 是 | — | `prd.md` | 须含 `## 约束` |
| `PRD-314` | warn | 是 | — | `prd.md` | 须含 `### 稳定性与性能` |
| `PRD-315` | warn | 是 | — | `prd.md` | 须含 `### 数据一致性` |
| `PRD-316` | warn | 是 | — | `prd.md` | `## 范围` 下须含 `**本次包含**`、`**明确不做**` |



### PRD → design 传导（语义）

| PRD 信号 | design 义务 |
|-----------|-------------|
| 窄触发且 `semantic_constraints[]` 非空 | [DES-S01～S05](./design-validate.md#17-语义校验des-s01s05)（按 `kind` 分支） |
| `excludes[]` 非空 | DES-S03 |
| `dimensions` 含 `one_of:` | DES-S01b |
| `SEM-*` id | `test_cases.covers` + `semantic_evidence.constraint_ref` |

**失败：** `route_after_prd_validate` → **pm**；violations 注入 PM prompt。

## 3.4 语义校验（PRD-S01～S06）

> 实现：`validators/prd_semantic_rules.py` · 默认 **blocking=error / advisory=warn** · Profile `validation.prd.semantic_block_on: warn` 可整体降级（legacy 兼容）。

| rule_id | 分级 | 严重度 | 触发 | 判定 |
|---------|------|--------|------|------|
| `PRD-S01` | blocking | error | 窄触发（见 semantic-validation 设计） | `semantic_constraints` 非空 |
| `PRD-S02` | blocking | error | 有 `semantic_constraints` | `source_ref` 引用存在的 US/FEAT/REQ |
| `PRD-S02b` | advisory | warn | 有 `semantic_constraints` | `dimensions` / `excludes[].rule` 符合规则语法白名单 |
| `PRD-S03` | advisory | warn | `scope_out` 非空 | scope_out 在 excludes 或 requirement_pool 有可匹配描述 |
| `PRD-S04` | advisory | warn | P0 FEAT 有 `user_story_ids` | FEAT 不得宽于 US（启发式） |
| `PRD-S05` | advisory | warn | 有 `semantic_constraints` | 每个 `SEM-*` 出现在 AC 或 requirement_pool 文本 |
| `PRD-S06` | advisory | warn | 有 `semantic_constraints` | `prd.md` 含 `## 语义约束` 且 id 一致 |
