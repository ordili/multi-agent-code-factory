# design_validate — 规则清单

> [quality-gates/README.md](./README.md) · JSON [artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md) · 模板 [artifact-templates/design-spec.md](../artifact-templates/design-spec.md) · [flow-spec.md](../artifact-templates/flow-spec.md)

**rule_id 合计：** **56** 条（§1 JSON **38** · §2 `design.md` / `*.mmd` **17** · §3 HITL **1**）

**表列图例：**

- **必检** — 是否执行该 rule：`是` = 每次 `design_validate` 均评估；`条件` = 仅当触发条件成立。key / `null` / `[]` / `""` 行为见 [空值与两层校验](#空值与两层校验)
- **触发条件** — 何时要求字段/章节非空；未触发时 JSON 可为 `[]`、MD 可省略子节；语义见 [design-spec](../artifact-schemas/design-spec.md) · [spec→design 传导](./spec-validate.md#spec--design-传导只读)
- **严重度** — 规则列 `error` / `warn`。**默认** Profile `validation.design.block_on: error`（与 [README §2](./README.md#2-profile-配置validation) 一致）。`design_validation.passed=false` **仅**当存在 **error** violation（**warn 不计入失败**）。默认：**有 error → 阻断**（`route_after_design_validate` → architect）；warn 只写入报告、不阻断
- **字段 · 判定** — 规则本体：JSON 路径或检查对象 + 通过/失败条件

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
| `modules`、`dev_tasks`、`traceability` 等 | 是 | **DES-001～009** 等 | 见 [§1](#1-designjsonerror--warn) |

---

## 1. design.json（error / warn）

### 1.1 任务与模块

| rule_id | 严重度 | 必检 | 触发条件 | 字段 | 判定 |
|---------|--------|------|----------|------|------|
| `DES-001` | error | 是 | — | `dev_tasks` | 非空 |
| `DES-002` | error | 是 | — | `dev_tasks[].id` | 唯一 |
| `DES-003` | error | 是 | — | `dev_tasks[].path`、`id`、`description` | 唯一 path；必填 |
| `DES-004` | error | 是 | — | `dev_tasks[].depends_on` | 引用已知 task id |
| `DES-005` | error | 是 | — | `dev_tasks` | 依赖无环 |
| `DES-006` | error | 是 | — | `modules` | 非空 |
| `DES-007` | error | 是 | — | `modules[]` | `name`、`path`、`responsibility`、`code_domain` 必填 |
| `DES-103` | error | 是 | — | `dev_tasks[].path`、`modules[].path` | 不得路径逃逸（`..` / 绝对路径） |
| `DES-104` | error | 条件 | `file_plan` 非空 | `file_plan[].path` | 须在 `dev_tasks[].path` 中 |

### 1.2 架构骨架与追溯

| rule_id | 严重度 | 必检 | 触发条件 | 字段 | 判定 |
|---------|--------|------|----------|------|------|
| `DES-008` | error | 是 | — | `non_goals`、`context_view`、`architecture.solution_strategy` | 非空 |
| `DES-009` | error | 是 | — | `traceability` | 非空；P0 `FEAT` 须在 `traceability` 或 `dev_tasks[].covers` 中可追溯 |
| `DES-010` | error | 是 | — | `cross_cutting` | 须存在（可为 `{}`） |
| `DES-101` | error | 条件 | 提供 spec | `traceability`、`dev_tasks[].covers` | 覆盖全部 `acceptance_criteria[].id` |
| `DES-102` | error | 条件 | spec 有 `scope_out` | `summary`、`modules[]` | 不得实现 scope_out 项 |

### 1.3 依赖、存储与 NFR

| rule_id | 严重度 | 必检 | 触发条件 | 字段 | 判定 |
|---------|--------|------|----------|------|------|
| `DES-011` | error | 条件 | spec `operational_profile` 含性能/可用性量化要求 | `non_functional` | 非空 |
| `DES-012` | error | 是 | — | `external_dependencies` | 非空（无中间件时显式 `filesystem`/`none`） |
| `DES-013` | error | 条件 | spec `context.storage` 为持久化 **或** design 含 `table_schemas` / `data_model` 项 | `table_schemas`、`data_model` | 非空或字段级 `columns` 齐全 |
| `DES-014` | error | 条件 | spec `consistency_profile.multi_writer=true` **或** 跨存储/多写场景 | `transaction_constraints` | 非空（**未触发**时不检，可为 `[]`） |
| `DES-018` | error | 条件 | `table_schemas[].columns[]` 非空 | `table_schemas[].columns[]` | 显式 `nullable`；`description` 非空 |
| `DES-019` | error | 条件 | `table_schemas[].storage` 为关系型 DB | `table_schemas[]` | 含 `created_at`、`updated_at`；索引或 `notes`；`version`（若 Profile 要求） |
| `DES-020` | warn | 条件 | `table_schemas[].indexes[]` 非空 | `indexes[]` | 每条含 `purpose` |
| `DES-027` | error | 是 | — | `modules[].code_domain` | 非空、格式合法、模块间不重复 |
| `DES-028` | error | 是 | — | `external_dependencies[]` | `code_domain` 规则（`none`/`filesystem`/中间件） |

### 1.4 图（diagrams[]）

| rule_id | 严重度 | 必检 | 触发条件 | 字段 | 判定 |
|---------|--------|------|----------|------|------|
| `DES-017` | error | 条件 | spec `context.storage` 为持久化 **或** `diagrams[]` 已登记任一条 | `diagrams[]` | **须**同时含 `kind=sequence` 与 `kind=flowchart`（可同文件多段） |

> **未触发**时 `diagrams` **可为 `[]`**（如无持久化 CLI、含多模块但未登记 `diagrams`）。多步业务流、design.md §4.7 人读要求见 **DES-206 / DES-217**（[§2](#2-designmd--mmd-格式p1)）。多模块拓扑图见 **DES-223**（`kind=context`，与 DES-017 无关）。文件层见 [§2.4](#24-mmd-图与-diagrams)（DES-203 / DES-214）。

### 1.5 错误目录与测试用例

| rule_id | 严重度 | 必检 | 触发条件 | 字段 | 判定 |
|---------|--------|------|----------|------|------|
| `DES-015` | error | 是 | — | `error_catalog` | 非空 |
| `DES-016` | error | 是 | — | `test_cases` | 非空 |
| `DES-016` | warn | 条件 | 提供 spec | `test_cases[].covers` | 每个 AC 宜有用例 `covers`（**DES-101** 对缺 cover 报 **error**，本条为温和提示） |
| `DES-021` | error | 是 | — | `error_catalog[].code`、`test_cases[]` | 每 code ≥1 条 `kind=negative` 且 `error_code` 匹配 |
| `DES-022` | warn | 是 | — | `test_cases[]` | 含 `happy`、`negative`、`boundary`；P0 FEAT/US 有 happy |
| `DES-023` | error | 是 | — | `error_catalog[].code` | 匹配 `^ERR-[A-Z][A-Z0-9_]{1,11}-\d{3}$` |
| `DES-024` | error | 是 | — | `test_cases[].id` | 匹配 `^TC-(HAP\|NEG\|BND)-[A-Z][A-Z0-9_]{1,11}-\d{3}$` |
| `DES-025` | error | 是 | — | `test_cases[].error_code` | 须存在于 `error_catalog[].code` |
| `DES-026` | warn | 是 | — | `test_cases[].kind`、`test_cases[].id` | `kind` 与 id 中段一致 |
| `DES-029` | error | 是 | — | `error_catalog[].code` | `{域}` 段在已注册域集合 |
| `DES-030` | error | 是 | — | `test_cases[].id` | `{域}` 段在已注册域集合 |
| `DES-031` | warn | 条件 | `kind=negative` 且填 `error_code` | `test_cases[]` | `error_code` 与 `id` 域段宜一致 |

### 1.6 接口

| rule_id | 严重度 | 必检 | 触发条件 | 字段 | 判定 |
|---------|--------|------|----------|------|------|
| `DES-032` | error | 是 | — | `interfaces[]`（顶层） | 每模块（`SYS` 豁免）至少一条；`module_ref` 匹配 `modules[].name` |
| `DES-033` | error | 是 | — | `interfaces[].operations[]` | 非空；`summary`、`inputs`、`outputs` 齐全 |
| `DES-034` | warn | 条件 | `operations[].errors[]` 非空 | `operations[].errors[]` | 须存在于 `error_catalog[].code` |

> **字段** 列与 [artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md) JSON 契约一致（英文键名）。

---

## 2. design.md / `*.mmd` 格式（P1）

Run `design.md` 须 **中文固定章节**（**§1–§6 + 附录 A–D**）；**不含** Rollout、方案对比专章、待澄清专章、监控专章。`design.md` §4 子节编号与 [artifact-templates/design-spec.md §4.x 映射](../artifact-templates/design-spec.md#4-子节--json按需可跳号) 一致。

### 2.1 固定章节（§1–§6 + 附录 A–D）

| rule_id | 严重度 | 必检 | 检查对象 | 判定 |
|---------|--------|------|----------|------|
| `DES-201` | warn | 是 | `design.md` | 须含 §1–§6 固定章节（见下「DES-201 章节」；JSON `test_cases` 非空时 **DES-016** 约束，不豁免 §6） |
| `DES-202` | warn | 是 | `design.md` | 须含附录 A–D（见下「DES-202 附录」） |
| `DES-207` | warn | 是 | `design.md` | 须含附录 D 代码对照（**DES-202** 已覆盖；Violations 宜与 DES-202 合并） |

**DES-201 章节（Markdown 二级标题，字面须含 `##` 前缀）：** 1. 背景与上下文 · 2. 设计目标 · 3. 非目标 · 4. 方案设计 · 6. 测试用例列表

**DES-202 附录（Markdown 二级标题，字面须含 `## 附录 X.` 前缀）：** A 需求追溯 · B 文件变更 · C 任务分解 · D 与现有代码对照

### 2.2 §4 子节（条件 warn）

按模板 **4.2 → 4.7** 顺序排列。

| rule_id | 严重度 | 必检 | 触发条件 | 判定 |
|---------|--------|------|----------|------|
| `DES-223` | warn | 条件 | 模块 ≥2 或 §4.4 有外部依赖 | 宜含 4.2 系统架构图 + architecture-*.mmd（见下「§4 子节标题」） |
| `DES-220` | warn | 条件 | `modules` 非空 | 须含 4.3 模块划分；表宜含 `code_domain` / 域前缀 |
| `DES-212` | warn | 条件 | 有中间件/第三方/`filesystem`（非仅 `none`） | 须含 4.4 外部依赖 |
| `DES-221` | warn | 条件 | `interfaces` 非空 | 须含 4.5 接口定义 |
| `DES-213` | warn | 条件 | 同 DES-013 | 须含 4.6 存储结构 |
| `DES-218` | warn | 条件 | §4.6 含列定义表 | 表宜含「可空」「注释」列 |
| `DES-216` | warn | 条件 | 同 DES-014 | §4.6 宜含「一致性与事务」段（四级标题或段落） |
| `DES-206` | warn | 条件 | 非线性 US / 跨模块 / 写了 `diagrams` 流程图 | 宜含 4.7 流程与时序 |
| `DES-217` | warn | 条件 | 同 DES-206 | §4.7 宜引用 `*.mmd` 且与 `diagrams[]` 一致 |

**§4 子节标题（Markdown 三级标题，字面须含 `###` 前缀）：** 4.2 系统架构图 · 4.3 模块划分 · 4.4 外部依赖 · 4.5 接口定义 · 4.6 存储结构 · 4.7 流程与时序

### 2.3 §5 / §6 与其它

| rule_id | 严重度 | 必检 | 触发条件 | 判定 |
|---------|--------|------|----------|------|
| `DES-224` | warn | 条件 | `non_functional` 非空或 spec §9 有 design 增量 | 宜含 5. 非功能性目标（二级标题，见上「DES-201 章节」格式） |
| `DES-219` | warn | 条件 | `test_cases` 非空 | 6. 测试用例列表表宜含「类型」列（happy / negative / boundary） |

### 2.4 *.mmd 图与 diagrams[]

| rule_id | 严重度 | 必检 | 触发条件 | 判定 |
|---------|--------|------|----------|------|
| `DES-203` | error* | 条件 | 同 DES-017 | `*.mmd` 可解析；Run **须**含 sequence + flowchart |
| `DES-204` | warn | 条件 | 存在 `*.mmd` | participant / 节点与 `modules` 名一致 |
| `DES-214` | error* | 条件 | 同 DES-017 | `diagrams[]` 登记 **须**与 Run 内 `*.mmd` 一致；同文件多段可登记多条 |

> **`DES-208`（非 rule_id）：** Run **不得**含 Rollout & Deployment 章节。  
> \* `DES-203` / `DES-214` 在 `validation.design.validate_mermaid: false` 时降为 warn 或跳过。

**规则未通过：** `route_after_design_validate` → **architect**；violations 注入 Architect prompt。

---

## 3. HITL 标志（DES-301）

| rule_id | 严重度 | 必检 | 触发条件 | 字段 | 判定 |
|---------|--------|------|----------|------|------|
| `DES-301` | — | 条件 | `hitl_flags` 命中 Profile.`require_hitl_if_flags` | `hitl_flags` | 标记 `require_hitl` → **design_hitl** |

人工审批见 [hitl.md](./hitl.md)；不替代 §1 / §2 规则修复。

---

## 空值与两层校验

「**必检 = 是**」= 进入 `design_validate` 后**每次都会评估**该 rule；**不等于** JSON 里必须显式写出该 key。空 key / `null` / `[]` / `""` 先经 **Pydantic 解析**，再经 **`DES-*` 规则**（实现见 `schemas/design.py` · `validators/`）。

### 两层门禁

| 阶段 | 时机 | 失败时 |
|------|------|--------|
| **Pydantic** | `DesignArtifact.model_validate(design.json)`（Architect 落盘前/后） | 缺 `version` / `spec_ref` / `revision`、类型非法 → **ValidationError**，**进不了** `design_validate` |
| **`DES-*` 规则** | `design_validate` 节点（Profile `validation.design.enabled: true`） | 写入 `design_validation.json`；默认 **error → `passed=false` → architect**（见上文 **严重度**） |

Profile `validation.design.enabled: false` 时跳过 **`DES-*`**，**仍**做 Pydantic 结构校验（见 [README §2](./README.md#2-profile-配置validation)）。

### §1 JSON：空值怎么读

**输入写法 → 内存值 → 是否报错**，按字段**形状**分三类；`key 缺失`、`null`、`[]` 在同一形状下**合并为一格**（不再逐行重复）。

**A. 列表字段** — `dev_tasks` · `modules` · `traceability` · `interfaces` · `error_catalog` · `test_cases` · `external_dependencies` 等。

| 输入（三者等价） | 内存值 | 判「非空」的 DES 规则 |
|----------------|--------|----------------------|
| key 缺失 · `null` · `[]` | `[]` | **error**（如 DES-001/006/009/012/015/016/032） |

列表**非空**但子项缺字段 / `""` → 由 **DES-003/007/033** 等**逐项**规则报错，不再重复「空列表」行。

**B. 对象 / 字符串字段**

| 字段 | 输入 | 内存值 | DES 规则 |
|------|------|--------|----------|
| `non_goals` | 缺失 · `null` · `[]` | `[]` | **DES-008** error |
| `context_view` | 缺失 · `null` · `{}` | `None` / `{}` | **DES-008** error（空即失败） |
| `architecture.solution_strategy` | 缺失 · `null` · `""` | 无有效字符串 | **DES-008** error |
| `modules[].name` 等嵌套必填 | `""` 或缺 key | `""` / 缺 | **DES-007** error |
| `summary` · `design_goals` | 缺失 · `null` · `[]` | `None` / `[]` | JSON **无** non-empty 规则（见 [JSON 契约 vs 规则](#json-契约-vs-规则与-schema是否必填对齐)） |

**C. 「须存在」与「条件可空」**

| 字段 | 输入 | 内存值 | DES 规则 |
|------|------|--------|----------|
| `cross_cutting` | 缺失 · `null` | `None` | **DES-010** error（须**存在**） |
| `cross_cutting` | `{}` | `{}` | **通过**（允许空对象） |
| `file_plan` | `[]` | `[]` | **DES-104 不触发**（仅非空时检 path） |
| `diagrams` | `[]` | `[]` | **DES-017 不触发**（未满足触发条件时可为 `[]`） |
| `transaction_constraints` | `[]` | `[]` | **DES-014 不触发**（未满足触发条件时可为 `[]`） |

> **必检 = 条件**（DES-013/014/017 等）：上表「不触发」= 触发条件列不成立时，不要求非空。

**Live 与 stub 差异** — **Live Architect** 在 validate 前 `enrich_design_for_validation`，可能自动补 `non_goals`、`context_view`、`architecture.solution_strategy`，并将 `cross_cutting: null` 设为 `{}`——空值**未必**落到 DES-008/010。**stub / fixture** 不 enrich，空值直接进上表判定。

**一句话** — 列表字段：缺/null/[] 等价 → 判非空则 error；`cross_cutting` 仅 null/缺失失败、`{}` 可过；条件规则未触发时 `[]` 允许；默认 error 阻断。

§2（`design.md` / `*.mmd`）：校 **Run 目录文件**（章节、`*.mmd`），不是 JSON key。缺章节多为 **warn**，默认**不**阻断（见上文 **严重度**）。

---

## 简单任务 vs 复杂任务

**不另设任务 tier。** 简单/复杂靠 **spec 信号** + **「必检 = 条件」** + [templates 极简 / 中等规模指引](../artifact-templates/design-spec.md#小任务--无持久化极简指引) 分化，**不是**靠 Profile 开关。

| 维度 | 简单（无持久化 CLI、单进程脚本等） | 复杂（持久化、多写、spec §9 有 NFR 增量等） |
|------|-----------------------------------|---------------------------------------------|
| **JSON · 必检 = 是** | 骨架始终检：`dev_tasks`、`modules`、`traceability`、`test_cases`、`error_catalog`、`external_dependencies`（`kind=none`）、`interfaces` 等 | **同左**（底线相同） |
| **JSON · 必检 = 条件** | **DES-013/014/011/017** 等**不触发** → `table_schemas`、`transaction_constraints`、`diagrams`、`non_functional` 可为 `[]` | 触发 → 须非空或满足判定 |
| **图（DES-017）** | spec 无持久化 **且** `diagrams[]` 为空 → **不触发**（双模块计算器 **不**因模块数 alone 触发） | spec 持久化 **或** 已登记 `diagrams[]` → **须** sequence + flowchart |
| **MD §4 子节** | **DES-201/202** 等固定 warn；**DES-212/213/206/223** 等**不触发** | design.md §4.4/4.6/4.7、§5 等按触发条件 warn |
| **阻断** | 仅 **error** 级 JSON 规则（默认 `block_on: error`）；§2 warn 不阻断 | 同左 |

> **必检 = 是** 只表示「每次都评估」，**不**表示简单任务可省略该字段；能否为空看 **判定** 列与 **触发条件** 列。

---

## 规范与实现对照

**消项用；非定稿规则来源。** 改 `validators/` 时以此表消项；**正文规则表不改**，除非 templates / schema 定稿变更。

| 区域 | 定稿规范（本文） | 当前实现（`validators/`） |
|------|------------------|---------------------------|
| **DES-017 / 203 / 214** | 条件：spec 持久化 **或** `diagrams[]` 已登记 → **须** sequence+flowchart（**不**因 `modules` 数量 alone 触发） | 实现 **无条件**要求 sequence+flowchart |
| **DES-032** | 顶层 `interfaces[]` | 已按顶层 `interfaces[]` 实现 |
| **DES-201** | §1–§6 + 附录 A–D | `design_md_rules.py` 仍检 **§1–§10** 旧章（含方案对比/横切/监控等） |
| **DES-202 / 207** | 附录 A–D | 仍检附录 **D=测试用例**、**E=代码对照** |
| **§4 子节编号** | 4.2 架构 / 4.3 模块 / 4.4 依赖 / 4.5 接口 / 4.6 存储 / 4.7 流程 | 仍用 **4.3 外部依赖**、**4.5 数据模型**、**4.6 流程** 等旧标题 |
| **DES-216** | §4.6「一致性与事务」 | 仍检 6.1 / 6.2 旧位置（三级标题） |
| **DES-219** | 6. 测试用例列表「类型」列 | 仍检附录 D + 8. 测试计划 分支 |
| **§6 / DES-201** | 6. 测试用例列表（不凭 JSON 豁免） | 实现仍引用 8. 测试计划 |
| **DES-224** | 条件 warn：5. 非功能性目标 | **未实现**（`design_md_rules.py` 无对应检查） |
| **§4 子节条件触发** | DES-212/213/216/221/223 等按「触发条件」列 | 实现 **多数 unconditional**（缺标题即告警，不看触发条件） |
| **DES-016 vs DES-101** | AC 覆盖：101=error，016=warn | 实现中两者均存在；101 优先作 hard gate |
| **summary / design_goals / code_delta** | schema 交付必填；见 [JSON 契约 vs 规则](#json-契约-vs-规则与-schema是否必填对齐) | JSON 层 **无** 对应 non-empty 规则（符合上表「定稿 JSON 规则」列） |
