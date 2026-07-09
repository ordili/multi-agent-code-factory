# design_validate — 规则清单

> **索引：** [quality-gates/README.md](./README.md)  
> **实现：** `multi_agent_code_factory/validators/design_rules.py` · `design_rules_extended.py` · `design_md_rules.py` · `mermaid.py`  
> **JSON 契约：** [artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md)  
> **人读模板：** [artifact-templates/design-spec.md](../artifact-templates/design-spec.md) · [flow-spec.md](../artifact-templates/flow-spec.md)

**rule_id 合计（定稿）：** **57** 条活跃（§4.1 JSON **38** · §4.2 `design.md` / `*.mmd` **18** · §4.4 HITL **1**）；**5** 条 MD 规则 **已废弃/合并**（见 [§4.2](#42-designmd--mmd-格式p1)）。

**任务 tier（`validators/task_tier.py`）：** 部分规则仅在「需要持久化 / 表结构 / 事务 / 流程图」时触发。无持久化 CLI（`is_stateless_design`）可跳过 **DES-013 / DES-014** 的 non-empty 判定；**省略 §4.7** 的小任务可跳过 **DES-017 / DES-203 / DES-214** 的 sequence+flowchart 硬性要求。详见 [design-spec 极简指引](../artifact-templates/design-spec.md#小任务--无持久化极简指引) 与 [flow-spec §何时需要产出图](../artifact-templates/flow-spec.md#何时需要产出图与-design-spec-对齐)。

> **必检** = 校验器是否执行该 rule_id；**触发条件** = 何时执行或何时要求字段/章节非空。  
> **本文规则表 = 定稿规范**（应与 [artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md) 及 templates 一致）。**当前 Python 实现若有偏差**，见 [§规范与实现对照](#规范与实现对照)（只读，改实现时消项）。

---

## JSON 契约 vs 规则（与 schema「是否必填」对齐）

[artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md) 的 **「是否必填 = 是」** 表示交付 intent；**本表 `DES-*`** 表示程序门禁。二者关系：

| 字段 | schema 是否必填 | 定稿 JSON 规则 | 说明 |
|------|----------------|----------------|------|
| `summary` | 是 | **无** non-empty 规则 | **DES-102** 仅在 spec 有 `scope_out` 时交叉检查 |
| `design_goals` | 是 | **无** | 人读 §2 由 **DES-201**（`design.md`）覆盖 |
| `file_plan` | 是 | **DES-104**（仅当非空） | 空 `[]` 不触发 path 一致性 |
| `architecture.code_delta` | 是 | **无** JSON 规则 | 人读附录 D 由 **DES-202 / DES-207** 覆盖 |
| `interfaces` | 是 | **DES-032**、**DES-033** | 顶层 `interfaces[]`；每模块（`SYS` 豁免）至少一条 |
| `modules`、`dev_tasks`、`traceability` 等 | 是 | **DES-001～009** 等 | 见 §4.1 |

---

## 4.1 JSON 结构（error / warn）

| rule_id | 严重度 | 必检 | 触发条件 | 字段 | 判定 |
|---------|--------|------|----------|------|------|
| `DES-001` | error | 是 | — | `dev_tasks` | 非空 |
| `DES-002` | error | 是 | — | `dev_tasks[].id` | 唯一 |
| `DES-003` | error | 是 | — | `dev_tasks[].path`、`id`、`description` | 唯一 path；必填 |
| `DES-004` | error | 是 | — | `dev_tasks[].depends_on` | 引用已知 task id |
| `DES-005` | error | 是 | — | `dev_tasks` | 依赖无环 |
| `DES-006` | error | 是 | — | `modules` | 非空 |
| `DES-007` | error | 是 | — | `modules[]` | `name`、`path`、`responsibility`、`code_domain` 必填 |
| `DES-008` | error | 是 | — | `non_goals`、`context_view`、`architecture.solution_strategy` | 非空 |
| `DES-009` | error | 是 | — | `traceability` | 非空；P0 `FEAT` 须在 `traceability` 或 `dev_tasks[].covers` 中可追溯 |
| `DES-010` | error | 是 | — | `cross_cutting` | 须存在（可为 `{}`） |
| `DES-011` | error | 条件 | spec `operational_profile` 非 trivial | `non_functional` | 非空 |
| `DES-012` | error | 是 | — | `external_dependencies` | 非空（无中间件时显式 `filesystem`/`none`） |
| `DES-013` | error | 条件 | `requires_table_schemas(design, spec)` | `table_schemas`、`data_model` | 非空或字段级 `columns` 齐全 |
| `DES-014` | error | 条件 | `requires_transaction_constraints(design, spec)` | `transaction_constraints` | 非空（**未触发**时不检，可为 `[]`） |
| `DES-015` | error | 是 | — | `error_catalog` | 非空 |
| `DES-016` | error | 是 | — | `test_cases` | 非空 |
| `DES-016` | warn | 条件 | 提供 spec | `test_cases[].covers` | 每个 AC 宜有用例 `covers`（**DES-101** 对缺 cover 报 **error**，本条为温和提示） |
| `DES-017` | error | 条件 | **非** `is_stateless_design` **且**（`diagrams[]` 非空 **或** 预期写 §4.7） | `diagrams[]` | 宜同时含 `kind=sequence` 与 `kind=flowchart`（可同文件多段）；stateless 且无 §4.7 时 **可为 `[]`** |
| `DES-018` | error | 条件 | `table_schemas[].columns[]` 非空 | `table_schemas[].columns[]` | 显式 `nullable`；`description` 非空 |
| `DES-019` | error | 条件 | `storage` 为关系型 DB | `table_schemas[]` | 含 `created_at`、`updated_at`；索引或 `notes`；`version`（若 `require_version`） |
| `DES-020` | warn | 条件 | `table_schemas[].indexes[]` 非空 | `indexes[]` | 每条含 `purpose` |
| `DES-021` | error | 是 | — | `error_catalog[].code`、`test_cases[]` | 每 code ≥1 条 `kind=negative` 且 `error_code` 匹配 |
| `DES-022` | warn | 是 | — | `test_cases[]` | 含 `happy`、`negative`、`boundary`；P0 FEAT/US 有 happy |
| `DES-023` | error | 是 | — | `error_catalog[].code` | 匹配 `^ERR-[A-Z][A-Z0-9_]{1,11}-\d{3}$` |
| `DES-024` | error | 是 | — | `test_cases[].id` | 匹配 `^TC-(HAP\|NEG\|BND)-[A-Z][A-Z0-9_]{1,11}-\d{3}$` |
| `DES-025` | error | 是 | — | `test_cases[].error_code` | 须存在于 `error_catalog[].code` |
| `DES-026` | warn | 是 | — | `test_cases[].kind`、`test_cases[].id` | `kind` 与 id 中段一致 |
| `DES-027` | error | 是 | — | `modules[].code_domain` | 非空、格式合法、模块间不重复 |
| `DES-028` | error | 是 | — | `external_dependencies[]` | `code_domain` 规则（`none`/`filesystem`/中间件） |
| `DES-029` | error | 是 | — | `error_catalog[].code` | `{域}` 段在已注册域集合 |
| `DES-030` | error | 是 | — | `test_cases[].id` | `{域}` 段在已注册域集合 |
| `DES-031` | warn | 条件 | `kind=negative` 且填 `error_code` | `test_cases[]` | `error_code` 与 `id` 域段宜一致 |
| `DES-032` | error | 是 | — | `interfaces[]`（顶层） | 每模块（`SYS` 豁免）至少一条；`module_ref` 匹配 `modules[].name` |
| `DES-033` | error | 是 | — | `interfaces[].operations[]` | 非空；`summary`、`inputs`、`outputs` 齐全 |
| `DES-034` | warn | 条件 | `operations[].errors[]` 非空 | `operations[].errors[]` | 须存在于 `error_catalog[].code` |
| `DES-101` | error | 条件 | 提供 spec | `traceability`、`dev_tasks[].covers` | 覆盖全部 `acceptance_criteria[].id` |
| `DES-102` | error | 条件 | spec 有 `scope_out` | `summary`、`modules[]` | 不得实现 scope_out 项 |
| `DES-103` | error | 是 | — | `dev_tasks[].path`、`modules[].path` | 不得路径逃逸（`..` / 绝对路径） |
| `DES-104` | error | 条件 | `file_plan` 非空 | `file_plan[].path` | 须在 `dev_tasks[].path` 中 |

> **字段** 列与 [artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md) JSON 契约一致（英文键名）。

---

## 4.2 design.md / `*.mmd` 格式（P1）

Run `design.md` 须 **中文固定章节**（**§1–§6 + 附录 A–D**）；**不含** Rollout、方案对比专章、待澄清专章、监控专章。§4 子节编号与 [artifact-templates/design-spec.md §4.x 映射](../artifact-templates/design-spec.md#4-子节--json按需可跳号) 一致。

### 硬必填章节（warn）

| rule_id | 严重度 | 必检 | 检查对象 | 判定 |
|---------|--------|------|----------|------|
| `DES-201` | warn | 是 | `design.md` | 须含 `## 1. 背景与上下文`、`## 2. 设计目标`、`## 3. 非目标`、`## 4. 方案设计`、`## 6. 测试用例列表`（原 **DES-209** 已合并入本条） |
| `DES-202` | warn | 是 | `design.md` | 须含 `## 附录 A.`～`## 附录 D.`（需求追溯 / 文件变更 / 任务分解 / 与现有代码对照） |
| `DES-207` | warn | 是 | `design.md` | 须含 `## 附录 D. 与现有代码对照`（可与 DES-202 合并告警） |
| `DES-215` | warn | 是 | `design.md` / `test_cases` | 须含 `## 6. 测试用例列表` 或 JSON `test_cases` 非空 |

### §4 子节（条件 warn）

| rule_id | 严重度 | 必检 | 触发条件 | 判定 |
|---------|--------|------|----------|------|
| `DES-220` | warn | 是 | `modules` 非空 | 须含 `### 4.3 模块划分`；表宜含 `code_domain` / 域前缀 |
| `DES-212` | warn | 条件 | 有中间件/第三方/`filesystem`（非仅 `none`） | 须含 `### 4.4 外部依赖` |
| `DES-221` | warn | 条件 | `interfaces` 非空 | 须含 `### 4.5 接口定义` |
| `DES-213` | warn | 条件 | `requires_table_schemas` | 须含 `### 4.6 存储结构` |
| `DES-218` | warn | 条件 | §4.6 含列定义表 | 表宜含「可空」「注释」列 |
| `DES-216` | warn | 条件 | `requires_transaction_constraints` | §4.6 宜含「一致性与事务」段（`####` 或段落） |
| `DES-206` | warn | 条件 | 非线性 US / 跨模块 / 写了 `diagrams` 流程图 | 宜含 `### 4.7 流程与时序` |
| `DES-217` | warn | 条件 | 同 DES-206 | §4.7 宜引用 `*.mmd` 且与 `diagrams[]` 一致 |
| `DES-223` | warn | 条件 | 模块 ≥2 或 §4.4 有外部依赖 | 宜含 `### 4.2 系统架构图` + `architecture-*.mmd`（`kind=context`） |

### §5 / §6 与其它

| rule_id | 严重度 | 必检 | 触发条件 | 判定 |
|---------|--------|------|----------|------|
| `DES-224` | warn | 条件 | `non_functional` 非空或 spec §9 有 design 增量 | 宜含 `## 5. 非功能性目标` |
| `DES-219` | warn | 是 | `test_cases` 非空 | `## 6. 测试用例列表` 表宜含「类型」列（happy / negative / boundary） |

### Mermaid / `diagrams[]`

| rule_id | 严重度 | 必检 | 触发条件 | 判定 |
|---------|--------|------|----------|------|
| `DES-203` | error* | 条件 | 同 DES-017（非 stateless 或已登记流程图） | `*.mmd` 可解析；Run 宜含 sequence + flowchart |
| `DES-204` | warn | 条件 | 存在 `*.mmd` | participant / 节点与 `modules` 名一致 |
| `DES-214` | error* | 条件 | 同 DES-017 | `diagrams[]` 登记与文件一致；同文件多段可登记多条 |

> **`DES-208`（非 rule_id）：** Run **不得**含 Rollout & Deployment 章节。  
> \* `DES-203` / `DES-214` 在 `validation.design.validate_mermaid: false` 时降为 warn 或跳过。

### 已废弃（定稿后不得要求）

| rule_id | 原判定 | 说明 |
|---------|--------|------|
| `DES-205` | `## 8. 测试计划` | → 由 **DES-215**（`## 6. 测试用例列表`）替代；**勿**再检 |
| `DES-210` | `## 10. 待澄清项` | 定稿 **无** 待澄清专章 |
| `DES-211` | `## 9. 监控与告警` | 定稿 **无** 监控专章 |
| `DES-222` | `## 5. 方案对比` | 方案对比 → **HITL / 评审**；§5 为 **非功能性目标**（选填） |
| `DES-209` | `## 3. 非目标` 独立 rule | 已合并入 **DES-201** |

旧版附录 **E**（代码对照）→ 现 **附录 D**；旧版附录 **D**（测试用例）→ 现 **§6**。

---

## 4.4 HITL 标志

| rule_id | 严重度 | 必检 | 触发条件 | 字段 | 判定 |
|---------|--------|------|----------|------|------|
| `DES-301` | — | 条件 | `hitl_flags` 命中 Profile.`require_hitl_if_flags` | `hitl_flags` | 标记 `require_hitl` → **design_hitl** |

**失败：** `route_after_design_validate` → **architect**；violations 注入 Architect prompt。

---

## 规范与实现对照

改 `validators/` 时以此表消项。**本文规则表不改**除非 templates / schema 定稿变更。

| 区域 | 定稿规范（本文） | 当前实现（`validators/`） |
|------|------------------|---------------------------|
| **DES-017 / 203 / 214** | 条件：`is_stateless_design` 等 tier | `design_rules_extended.py` / `mermaid.py` **无条件**要求 sequence+flowchart |
| **DES-032** | 顶层 `interfaces[]` | 已按顶层 `interfaces[]` 实现 |
| **DES-201** | §1–§6 + 附录 A–D | `design_md_rules.py` 仍检 **§1–§10** 旧章（含方案对比/横切/监控等） |
| **DES-202 / 207 / 215** | 附录 A–D；§6 测试用例 | 仍检附录 **D=测试用例**、**E=代码对照** |
| **§4 子节编号** | 4.3 模块 / 4.4 依赖 / 4.5 接口 / 4.6 存储 / 4.7 流程 | 仍用 **4.3 外部依赖**、**4.5 数据模型**、**4.6 流程** 等旧标题 |
| **DES-216** | §4.6「一致性与事务」 | 仍检 `### 6.1` / `### 6.2` 旧位置 |
| **DES-219** | `## 6. 测试用例列表`「类型」列 | 仍检附录 D + `## 8. 测试计划` 分支 |
| **DES-205** | 已废弃 | 实现仍引用 `## 8. 测试计划` |
| **DES-224** | 条件 warn：`## 5. 非功能性目标` | **未实现**（`design_md_rules.py` 无对应检查） |
| **§4 子节条件触发** | DES-212/213/216/221/223 等按 tier / 字段非空触发 | `design_md_rules.py` **多数 unconditional**（缺标题即告警，不看触发条件） |
| **DES-016 vs DES-101** | AC 覆盖：101=error，016=warn | 实现中两者均存在；101 优先作 hard gate |
| **summary / design_goals / code_delta** | schema 交付必填；见上表 | JSON 层 **无** 对应 non-empty 规则（符合上表「定稿 JSON 规则」列） |
