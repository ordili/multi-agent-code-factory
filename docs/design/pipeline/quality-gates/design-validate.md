# design_validate — 规则清单

## 依赖上游文档（只读）

审查 / 修订本文时 **仅以本表及正文规则表为准**；不引用 `validators/` 等下游实现。按流水线先后与 **schemas → templates → 配置** 分组排列。


| 分类          | 上游文档                                                                                                   | 定位                                                                                                                                   |
| ----------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| **spec 基线** | [artifact-schemas/prd-spec.md](../artifact-schemas/prd-spec.md)                                        | Run `spec.json` 字段定义；DES-101/102/011/013/014/017 等交叉校验的 spec 信号来源。                                                                   |
| **spec 基线** | [spec-validate.md §传导](./spec-validate.md#spec--design-传导只读)                                           | spec 信号 → design 义务只读对照（§1 条件规则触发基线；字段细节查 prd-spec）。                                                                                 |
| **JSON 契约** | [artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md)                                  | Run `design.json` 的 JSON 字段、类型、coerce 与 `ERR-*` / `TC-*` 标识符约定（§1 规则依据）。                                                               |
| **人读模板**    | [artifact-templates/design-spec.md](../artifact-templates/design-spec.md)                              | Run `design.md` 固定章节、附录与 §4.x 子节写作模板（§2.1–2.3 规则依据）。                                                                                 |
| **人读模板**    | [artifact-templates/flow-spec.md](../artifact-templates/flow-spec.md)                                  | Run `*.mmd` 图种类、命名约定与 `diagrams[]` 登记写法（§2.4 规则依据）。                                                                                  |
| **校验产出**    | [artifact-schemas/validation-report-spec.md](../artifact-schemas/validation-report-spec.md)            | `design_validate` 产出的 `design_validation.json` 报告结构与 `passed` 语义。                                                                    |
| **运行配置**    | [quality-gates/README.md §2](./README.md#2-profile-配置validation)                                       | `validation.design.*`（`enabled`、`block_on`、`validate_mermaid`、`require_hitl_if_flags` 等）开关语义；YAML 载体见 [profiles.md](../profiles.md)。 |
| **流水线**     | [multi-agent-pipeline-design.md §4.1.2](../multi-agent-pipeline-design.md#412-产物校验与-hitlpm--architect) | `design_validate` 在流水线中的位置、与 PM/Architect 环关系及失败后回路。                                                                                 |


**rule_id 合计：** **55** 条（§1 JSON **38** · §2 `design.md` / `*.mmd` **16** · §3 HITL **1**）

**表列图例：** `必检` · `触发条件` · `严重度` · `字段` / `判定`（§2 为 `检查对象`）


| 列           | 含义                                                                                                         |
| ----------- | ---------------------------------------------------------------------------------------------------------- |
| **必检**      | `是` = 每次 `design_validate` 都评估；`条件` = 仅「触发条件」成立时评估                                                         |
| **触发条件**    | 何时要求非空；`—` = 无额外前提。未触发时 JSON 可 `[]`、MD 可省略子节（[传导表](./spec-validate.md#spec--design-传导只读) · [空值](#空值与两层校验)） |
| **严重度**     | `error` 默认令 `passed=false` 并回 Architect；`warn` 只写入报告（[README §2](./README.md#2-profile-配置validation)）      |
| **字段 / 判定** | 查什么 + 怎样算通过                                                                                                |


> 无任务 tier；能否省略字段/章节只看「触发条件」。写作范例见 [templates 小任务指引](../artifact-templates/design-spec.md#小任务--无持久化极简指引)。

> **本文规则表 = 定稿规范**（应与 [artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md) 及 templates 一致）。

---

## JSON 契约 vs 规则（与 schema「是否必填」对齐）

[artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md) 的 **「是否必填 = 是」** 表示交付 intent；**本表 `DES-*`** 表示程序门禁。二者关系：


| 字段                                     | schema 是否必填 | 定稿 JSON 规则              | 说明                                                                             |
| -------------------------------------- | ----------- | ----------------------- | ------------------------------------------------------------------------------ |
| `summary`                              | 是           | **无** non-empty 规则      | **DES-102** 仅在 [prd-spec `scope_out`](../artifact-schemas/prd-spec.md) 非空时交叉检查 |
| `design_goals`                         | 是           | **无**                   | 人读 §2 由 **DES-201**（`design.md`）覆盖                                             |
| `file_plan`                            | 是           | **DES-104**（仅当非空）       | 空 `[]` 不触发 path 一致性                                                            |
| `architecture.code_delta`              | 是           | **无** JSON 规则           | 人读附录 D 由 **DES-202** 覆盖                                                        |
| `interfaces`                           | 是           | **DES-032**、**DES-033** | 顶层 `interfaces[]`；每模块（`code_domain=SYS` 豁免，见 §1.6 脚注）至少一条                      |
| `modules`、`dev_tasks`、`traceability` 等 | 是           | **DES-001～009** 等       | 见 [§1](#1-designjsonerror--warn)                                               |


---

## 1. design.json（error / warn）

### 1.1 任务与模块


| rule_id   | 严重度   | 必检  | 触发条件           | 字段                                    | 判定                                              |
| --------- | ----- | --- | -------------- | ------------------------------------- | ----------------------------------------------- |
| `DES-001` | error | 是   | —              | `dev_tasks`                           | 非空                                              |
| `DES-002` | error | 是   | —              | `dev_tasks[].id`                      | 唯一                                              |
| `DES-003` | error | 是   | —              | `dev_tasks[].path`、`id`、`description` | 唯一 path；必填                                      |
| `DES-004` | error | 是   | —              | `dev_tasks[].depends_on`              | 引用已知 task id                                    |
| `DES-005` | error | 是   | —              | `dev_tasks`                           | 依赖无环                                            |
| `DES-006` | error | 是   | —              | `modules`                             | 非空                                              |
| `DES-007` | error | 是   | —              | `modules[]`                           | `name`、`path`、`responsibility`、`code_domain` 必填 |
| `DES-103` | error | 是   | —              | `dev_tasks[].path`、`modules[].path`   | 不得路径逃逸（`..` / 绝对路径）                             |
| `DES-104` | error | 条件  | `file_plan` 非空 | `file_plan[].path`                    | 须在 `dev_tasks[].path` 中                         |


### 1.2 架构骨架与追溯


| rule_id   | 严重度   | 必检  | 触发条件                                                           | 字段                                                          | 判定                                                         |
| --------- | ----- | --- | -------------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------- |
| `DES-008` | error | 是   | —                                                              | `non_goals`、`context_view`、`architecture.solution_strategy` | 非空                                                         |
| `DES-009` | error | 是   | —                                                              | `traceability`                                              | 非空；P0 `FEAT` 须在 `traceability` 或 `dev_tasks[].covers` 中可追溯 |
| `DES-010` | error | 是   | —                                                              | `cross_cutting`                                             | 须存在（可为 `{}`）                                               |
| `DES-101` | error | 条件  | Run 含 `spec.json`（[prd-spec](../artifact-schemas/prd-spec.md)） | `traceability`、`dev_tasks[].covers`                         | 覆盖全部 `acceptance_criteria[].id`                            |
| `DES-102` | error | 条件  | [prd-spec `scope_out`](../artifact-schemas/prd-spec.md) 非空   | `summary`、`modules[]`                                       | 不得实现 scope_out 项                                           |


### 1.3 依赖、存储与 NFR

> **spec 侧信号：** 字段定义见 [prd-spec.md](../artifact-schemas/prd-spec.md)；与 design 义务对照见 [spec→design 传导](./spec-validate.md#spec--design-传导只读)（只读）。


| rule_id   | 严重度   | 必检  | 触发条件                                                                       | 字段                           | 判定                                                              |
| --------- | ----- | --- | -------------------------------------------------------------------------- | ---------------------------- | --------------------------------------------------------------- |
| `DES-011` | error | 条件  | 传导表：`operational_profile` 含性能/可用性量化要求                                      | `non_functional`             | 非空                                                              |
| `DES-012` | error | 是   | —                                                                          | `external_dependencies`      | 非空（无中间件时显式 `filesystem`/`none`）                                 |
| `DES-013` | error | 条件  | 传导表：`context.storage` 持久化；**或** design 已含 `table_schemas` / `data_model` 项 | `table_schemas`、`data_model` | 非空或字段级 `columns` 齐全                                             |
| `DES-014` | error | 条件  | 传导表：`consistency_profile.multi_writer=true` 或多写场景                          | `transaction_constraints`    | 非空（**未触发**时不检，可为 `[]`）                                          |
| `DES-018` | error | 条件  | `table_schemas[].columns[]` 非空                                             | `table_schemas[].columns[]`  | 显式 `nullable`；`description` 非空                                  |
| `DES-019` | error | 条件  | `table_schemas[].storage` 为关系型 DB                                          | `table_schemas[]`            | 含 `created_at`、`updated_at`；索引或 `notes`；`version`（若 Profile 要求） |
| `DES-020` | warn  | 条件  | `table_schemas[].indexes[]` 非空                                             | `indexes[]`                  | 每条含 `purpose`                                                   |
| `DES-027` | error | 是   | —                                                                          | `modules[].code_domain`      | 非空、格式合法、模块间不重复                                                  |
| `DES-028` | error | 是   | —                                                                          | `external_dependencies[]`    | `code_domain` 规则（`none`/`filesystem`/中间件）                       |


### 1.4 图（diagrams[]）


| rule_id   | 严重度   | 必检  | 触发条件                                                | 字段           | 判定                                                  |
| --------- | ----- | --- | --------------------------------------------------- | ------------ | --------------------------------------------------- |
| `DES-017` | error | 条件  | 传导表：`context.storage` 持久化；**或** `diagrams[]` 已登记任一条 | `diagrams[]` | **须**同时含 `kind=sequence` 与 `kind=flowchart`（可同文件多段） |


> **未触发**时 `diagrams` **可为 `[]`**（如无持久化 CLI、含多模块但未登记 `diagrams`）。**已登记任一条**（含仅 `kind=context`）即触发，须补全 `sequence` + `flowchart`；`context` 拓扑人读义务见 **DES-223**。多步业务流、§4.7 人读要求见 **DES-206 / DES-217**（[§2](#22-4-子节条件-warn)）。文件层见 [§2.4](#24-mmd-图与-diagrams)（DES-203 / DES-214）。

### 1.5 错误目录与测试用例


| rule_id   | 严重度   | 必检  | 触发条件                            | 字段                                    | 判定                                                                              |
| --------- | ----- | --- | ------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------- |
| `DES-015` | error | 是   | —                               | `error_catalog`                       | 非空                                                                              |
| `DES-016` | error | 是   | —                               | `test_cases`                          | 非空                                                                              |
| `DES-016` | warn  | 条件  | Run 含 `spec.json`               | `test_cases[].covers`                 | 每个 AC 宜有用例 `covers`（**DES-101** 对缺 cover 报 **error**，本条为温和提示）                   |
| `DES-021` | error | 是   | —                               | `error_catalog[].code`、`test_cases[]` | 每 code ≥1 条 `kind=negative` 且 `error_code` 匹配                                   |
| `DES-022` | warn  | 是   | —                               | `test_cases[]`                        | 含 `happy`、`negative`、`boundary`；P0 FEAT/US 有 happy                              |
| `DES-023` | error | 是   | —                               | `error_catalog[].code`                | 匹配 `^ERR-[A-Z][A-Z0-9_]{1,11}-\d{3}$`                                           |
| `DES-024` | error | 是   | —                               | `test_cases[].id`                     | 匹配 `^TC-(HAP\|NEG\|BND)-[A-Z][A-Z0-9_]{1,11}-\d{3}$`                           |
| `DES-025` | error | 是   | —                               | `test_cases[].error_code`             | 须存在于 `error_catalog[].code`                                                     |
| `DES-026` | warn  | 是   | —                               | `test_cases[].kind`、`test_cases[].id` | `kind` 与 id 中段一致                                                                |
| `DES-029` | error | 是   | —                               | `error_catalog[].code`                | `{域}` 段在已注册域集合（见 [design-spec 标识符约定](../artifact-schemas/design-spec.md#标识符约定)） |
| `DES-030` | error | 是   | —                               | `test_cases[].id`                     | `{域}` 段在已注册域集合（同上）                                                              |
| `DES-031` | warn  | 条件  | `kind=negative` 且填 `error_code` | `test_cases[]`                        | `error_code` 与 `id` 域段宜一致                                                       |


### 1.6 接口


| rule_id   | 严重度   | 必检  | 触发条件                       | 字段                          | 判定                                                             |
| --------- | ----- | --- | -------------------------- | --------------------------- | -------------------------------------------------------------- |
| `DES-032` | error | 是   | —                          | `interfaces[]`（顶层）          | 每模块至少一条；`module_ref` 匹配 `modules[].name`（`code_domain=SYS` 豁免） |
| `DES-033` | error | 是   | —                          | `interfaces[].operations[]` | 非空；`summary`、`inputs`、`outputs` 齐全                             |
| `DES-034` | warn  | 条件  | `operations[].errors[]` 非空 | `operations[].errors[]`     | 须存在于 `error_catalog[].code`                                    |


> **`SYS`：** `modules[].code_domain` 取字面 `SYS` 的横切/基础设施模块，可无 `interfaces[]` 条目（见 [design-spec §interfaces](../artifact-schemas/design-spec.md#字段)）。

> **字段** 列与 [artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md) JSON 契约一致（英文键名）。

---

## 2. design.md / `*.mmd` 格式（P1）

Run `design.md` 须 **中文固定章节**（**§1–§6 + 附录 A–D**）；**不含** Rollout、方案对比专章、待澄清专章、监控专章。`design.md` §4 子节编号与 [artifact-templates/design-spec.md §4.x 映射](../artifact-templates/design-spec.md#4-子节--json按需可跳号) 一致。

### 2.1 固定章节（§1–§6 + 附录 A–D）


| rule_id   | 严重度  | 必检  | 检查对象        | 判定                                                                        |
| --------- | ---- | --- | ----------- | ------------------------------------------------------------------------- |
| `DES-201` | warn | 是   | `design.md` | 须含 §1–§6 固定章节（见下「DES-201 章节」；JSON `test_cases` 非空时 **DES-016** 约束，不豁免 §6） |
| `DES-202` | warn | 是   | `design.md` | 须含附录 A–D（见下「DES-202 附录」；附录 D = 与现有代码对照）                                  |


**DES-201 章节（Markdown 二级标题，字面须含 `##` 前缀）：** 1. 背景与上下文 · 2. 设计目标 · 3. 非目标 · 4. 方案设计 · 6. 测试用例列表

**DES-202 附录（Markdown 二级标题，字面须含 `## 附录 X.` 前缀）：** A 需求追溯 · B 文件变更 · C 任务分解 · D 与现有代码对照

### 2.2 §4 子节（条件 warn）

按模板 **4.2 → 4.7** 顺序排列。


| rule_id   | 严重度  | 必检  | 触发条件                                                       | 判定                                             |
| --------- | ---- | --- | ---------------------------------------------------------- | ---------------------------------------------- |
| `DES-223` | warn | 条件  | `modules` ≥2 **或** `external_dependencies` 含 `kind≠none` 项 | 宜含 4.2 系统架构图 + architecture-*.mmd（见下「§4 子节标题」） |
| `DES-220` | warn | 条件  | `modules` 非空                                               | 须含 4.3 模块划分；表宜含 `code_domain` / 域前缀            |
| `DES-212` | warn | 条件  | 有中间件/第三方/`filesystem`（非仅 `none`）                           | 须含 4.4 外部依赖                                    |
| `DES-221` | warn | 条件  | `interfaces` 非空                                            | 须含 4.5 接口定义                                    |
| `DES-213` | warn | 条件  | 同 DES-013                                                  | 须含 4.6 存储结构                                    |
| `DES-218` | warn | 条件  | §4.6 含列定义表                                                 | 表宜含「可空」「注释」列                                   |
| `DES-216` | warn | 条件  | 同 DES-014                                                  | §4.6 宜含「一致性与事务」段（四级标题或段落）                      |
| `DES-206` | warn | 条件  | 非线性 US / 跨模块协作                                             | 宜含 4.7 流程与时序                                   |
| `DES-217` | warn | 条件  | 同 DES-206                                                  | §4.7 宜引用 `*.mmd` 且与 `diagrams[]` 一致            |


> **与 DES-017：** 持久化或已登记 `diagrams[]` 时 **DES-017**（**error**）要求 JSON 含 `sequence` + `flowchart`，**不**自动要求人读 §4.7。简单 CRUD 可有 JSON 图而无 §4.7 专节；**DES-206** 仅按 US 路径复杂度（非线性 / 跨模块）**warn** §4.7。

**§4 子节标题（Markdown 三级标题，字面须含 `###` 前缀）：** 4.2 系统架构图 · 4.3 模块划分 · 4.4 外部依赖 · 4.5 接口定义 · 4.6 存储结构 · 4.7 流程与时序

### 2.3 §5 / §6 与其它


| rule_id   | 严重度  | 必检  | 触发条件                                        | 判定                                             |
| --------- | ---- | --- | ------------------------------------------- | ---------------------------------------------- |
| `DES-224` | warn | 条件  | `non_functional` 非空；或传导表 DES-011 同类 spec 信号 | 宜含 5. 非功能性目标（二级标题，见上「DES-201 章节」格式）            |
| `DES-219` | warn | 条件  | `test_cases` 非空                             | 6. 测试用例列表表宜含「类型」列（happy / negative / boundary） |


### 2.4 *.mmd 图与 diagrams[]


| rule_id   | 严重度    | 必检  | 触发条件       | 判定                                                 |
| --------- | ------ | --- | ---------- | -------------------------------------------------- |
| `DES-203` | error* | 条件  | 同 DES-017  | `*.mmd` 可解析；Run **须**含 sequence + flowchart        |
| `DES-204` | warn   | 条件  | 存在 `*.mmd` | participant / 节点与 `modules` 名一致                    |
| `DES-214` | error* | 条件  | 同 DES-017  | `diagrams[]` 登记 **须**与 Run 内 `*.mmd` 一致；同文件多段可登记多条 |


> **DES-208**（非 rule_id）：Run **不得**含 Rollout & Deployment 章节。  
> **DES-203** / **DES-214** 在 Profile `validation.design.validate_mermaid: false` 时降为 warn 或跳过（见 [README §2](./README.md#2-profile-配置validation)）。

**JSON error 未通过：** 默认阻断并回 Architect（见上文 **严重度** · [主线 §4.1.2](../multi-agent-pipeline-design.md#412-产物校验与-hitlpm--architect)）。§2 **warn** 默认不令 `passed=false`。

---

## 3. HITL 标志（DES-301）


| rule_id   | 严重度 | 必检  | 触发条件                                            | 字段           | 判定                                  |
| --------- | --- | --- | ----------------------------------------------- | ------------ | ----------------------------------- |
| `DES-301` | —   | 条件  | `hitl_flags` 命中 Profile.`require_hitl_if_flags` | `hitl_flags` | 标记 `require_hitl` → **design_hitl** |


人工审批见 [hitl.md](./hitl.md)；不替代 §1 / §2 规则修复。

---

## 空值与两层校验

「**必检 = 是**」= 进入 `design_validate` 后**每次都会评估**该 rule；**不等于** JSON 里必须显式写出该 key。空 key / `null` / `[]` / `""` 先经 [design-spec JSON 归一化（coerce）](../artifact-schemas/design-spec.md#json-归一化coerce)，再经 **`DES-*` 规则**评估。

### 两层门禁


| 阶段             | 时机                                                                                                                                               | 失败时                                                                                                                                       |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **JSON 结构校验**  | 落盘 `design.json` 解析为 [design-spec](../artifact-schemas/design-spec.md) 契约对象（见 [Pydantic 结构必填](../artifact-schemas/design-spec.md#pydantic-结构必填)） | 缺 `spec_ref`、类型非法等 → **不进** `design_validate`                                                                                             |
| **`DES-*` 规则** | `design_validate` 节点（Profile `validation.design.enabled: true`）                                                                                  | 写入 [validation-report `design_validation.json`](../artifact-schemas/validation-report-spec.md)；默认 **error → `passed=false`**（见上文 **严重度**） |


Profile `validation.design.enabled: false` 时跳过 **`DES-*`**，**仍**做 JSON 结构校验（见 [README §2](./README.md#2-profile-配置validation)）。

### §1 JSON：空值怎么读

**输入写法 → 内存值 → 是否报错**，按字段**形状**分三类；`key 缺失`、`null`、`[]` 在同一形状下**合并为一格**（不再逐行重复）。

**A. 列表字段** — `dev_tasks` · `modules` · `traceability` · `interfaces` · `error_catalog` · `test_cases` · `external_dependencies` 等。


| 输入（三者等价）               | 内存值  | 判「非空」的 DES 规则                                |
| ---------------------- | ---- | -------------------------------------------- |
| key 缺失 · `null` · `[]` | `[]` | **error**（如 DES-001/006/009/012/015/016/032） |


列表**非空**但子项缺字段 / `""` → 由 **DES-003/007/033** 等**逐项**规则报错，不再重复「空列表」行。

**B. 对象 / 字符串字段**


| 字段                               | 输入                 | 内存值           | DES 规则                                                                   |
| -------------------------------- | ------------------ | ------------- | ------------------------------------------------------------------------ |
| `non_goals`                      | 缺失 · `null` · `[]` | `[]`          | **DES-008** error                                                        |
| `context_view`                   | 缺失 · `null` · `{}` | `None` / `{}` | **DES-008** error（空即失败）                                                  |
| `architecture.solution_strategy` | 缺失 · `null` · `""` | 无有效字符串        | **DES-008** error                                                        |
| `modules[].name` 等嵌套必填           | `""` 或缺 key        | `""` / 缺      | **DES-007** error                                                        |
| `summary` · `design_goals`       | 缺失 · `null` · `[]` | `None` / `[]` | JSON **无** non-empty 规则（见 [JSON 契约 vs 规则](#json-契约-vs-规则与-schema是否必填对齐)） |


**C. 「须存在」与「条件可空」**


| 字段                             | 输入          | 内存值      | DES 规则                                     |
| ------------------------------ | ----------- | -------- | ------------------------------------------ |
| `cross_cutting`                | 缺失 · `null` | `None`   | **DES-010** error（须**存在**）                 |
| `cross_cutting`                | `{}`        | `{}`     | **通过**（允许空对象）                              |
| `file_plan`                    | `[]`        | `[]`     | **DES-104 不触发**（仅非空时检 path）                |
| `diagrams`                     | `[]`        | `[]`     | **DES-017 不触发**（未满足触发条件时可为 `[]`）           |
| `transaction_constraints`      | `[]`        | `[]`     | **DES-014 不触发**（未满足触发条件时可为 `[]`）           |
| `table_schemas` · `data_model` | `[]`        | `[]`     | **DES-013 不触发**（传导表未要求持久化且 design 未自登记表项时） |
| `non_functional`               | `[]` / 缺    | `[]` / 缺 | **DES-011 不触发**（传导表未要求 NFR 增量时）            |


> **必检 = 条件**（DES-013/014/011/017 等）：上表「不触发」= [§1](#1-designjsonerror--warn)「触发条件」列不成立时，不要求非空。

**一句话** — 列表字段：缺/null/[] 等价 → 判非空则 error；`cross_cutting` 仅 null/缺失失败、`{}` 可过；条件规则未触发时 `[]` 允许；默认 error 阻断。coerce 后的形状见 [design-spec §JSON 归一化](../artifact-schemas/design-spec.md#json-归一化coerce)。

§2（`design.md` / `*.mmd`）：校 **Run 目录文件**（章节、`*.mmd`），不是 JSON key。缺章节多为 **warn**，默认**不**阻断（见上文 **严重度**）。