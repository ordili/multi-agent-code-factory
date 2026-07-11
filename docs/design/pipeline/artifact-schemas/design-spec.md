# design-spec.md — DesignArtifact（Architect JSON 契约）

## 依赖上游文档（只读）

审查 / 修订本文时 **以本表、正文字段定义及同名上游人读 § 映射为准**。`quality-gates/` 为**下游**，不在此表列出（见 [README.md §单向依赖](../README.md#1-单向依赖)）。


| 分类             | 上游文档                                                                      | 定位                                      |
| -------------- | ------------------------------------------------------------------------- | --------------------------------------- |
| **总设计**        | [multi-agent-pipeline-design.md](../multi-agent-pipeline-design.md)       | 系统的总体设计书                                |
| **上游 JSON 契约** | [prd-spec.md](./prd-spec.md)                                              | 上游 JSON 契约 prd-spec.md（Run `prd.json`） |
| **人读模板**       | [artifact-templates/design-spec.md](../artifact-templates/design-spec.md) | 上游人读 design-spec.md                     |
| **运行配置**       | [profiles.md](../profiles.md)                                             | Profile 注入相关字段语境                        |


---

> **实现：** `multi_agent_code_factory/schemas/design.py`  
> **Run 落盘：** `docs/runs/<task_id>/design.json`  
> **上游 Run：** 同目录 `prd.json`（字段定义见 [prd-spec.md](./prd-spec.md)）

机器可读契约以 **本文 + Pydantic** 为准。

---



## 文档角色


| 项        | 说明                                                                |
| -------- | ----------------------------------------------------------------- |
| **定义对象** | 单次 Run 的 `design.json`（Architect 结构化输出），不是规范文件名本身                 |
| **键名**   | 英文 snake_case / 枚举字面量（给 Structured Output、校验器、下游 Agent）           |
| **字符串值** | **宜中文**（摘要、说明、场景等）；标识符与路径保持英文（见 [语言约定](#语言约定)）                    |
| **不定义**  | Run `design.md` 章节、写作篇幅、Profile 选用（姊妹目录 `artifact-templates/` 规定） |


**数据流：** PM 产出 `prd.json` → Architect 读 `prd.json` 产出 `design.json` → 渲染 `design.md` / 登记 `*.mmd`。下游 Developer / QA **以 JSON 为准**。

---



## 语言约定


| 部分                     | 语言  | 示例                                                |
| ---------------------- | --- | ------------------------------------------------- |
| JSON **键**             | 英文  | `modules`、`test_cases`                            |
| **标识符**                | 英文  | `FEAT-1`、`ERR-CLI-001`、`TC-HAP-CLI-001`           |
| **代码路径**               | 英文  | `src/cli.py`、`go.mod`、`pom.xml`（相对 `code_root`；布局随 Profile，见 [dev_tasks[]](#dev_tasks执行计划)） |
| **说明类字符串值**            | 中文  | `summary`、`error_catalog[].when`                  |
| Run `design.md` **正文** | 中文  | 由渲染器自 JSON 生成；人读格式见 `artifact-templates/` 同名 spec |


---



## Pydantic 结构必填

下列键 **缺则** `DesignArtifact.model_validate` **失败**（`coerce_design_payload` 可补 `version` / `revision`；其余键有默认值或可为 `null` / `[]`）：


| 字段         | 类型          | 默认              |
| ---------- | ----------- | --------------- |
| `version`  | `"1"`       | coerce 可补 `"1"` |
| `spec_ref` | string      | 无               |
| `revision` | integer ≥ 1 | coerce 可补 `1`   |


---



## JSON 归一化（coerce）

实现：`schemas/design.py` 中 `coerce_design_payload`（Pydantic `before` validator）。在解析 JSON 时 **就地** 修正常见 LLM 形状，**不改变** 字段语义：


| 行为                | 说明                                                                                                                              |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| 顶层别名合并            | `decisions` → `architecture.decisions`；`code_delta` → `architecture.code_delta`；`test_strategy` → `cross_cutting.test_strategy` |
| 缺省元数据             | 无 `version` / `revision` 时补 `"1"` / `1`                                                                                         |
| 列表字段              | `modules`、`interfaces` 等：标量或单对象 → 包成数组                                                                                          |
| 字符串列表             | `design_goals`、`non_goals`、`hitl_flags`：单字符串 → 单元素数组                                                                            |
| `error_catalog[]` | 项内 `error_code` → `code`                                                                                                        |
| `non_functional`  | 单对象 → 单元素数组                                                                                                                     |
| `diagrams[].kind` | 别名归一（如 `sequence diagram` → `sequence`）                                                                                         |


---



## 字段

**「是否必填」列：**


| 值     | 含义                                                    |
| ----- | ----------------------------------------------------- |
| **是** | 规范交付 intent：须写出实质内容；空 `[]` / `{}` / 空字符串不算完成（说明列例外除外） |
| **否** | 可不写字段；或说明列写明无相关场景时 `[]` / 省略可接受                       |


缺键即 Pydantic 报错的字段见 [Pydantic 结构必填](#pydantic-结构必填)。

**与校验层的关系：** 「是否必填」表达 **交付 intent**（与人读 `design.md` 的 JSON 映射一致，映射表在 `artifact-templates/` 同名 spec）。与当前 JSON 校验 **不完全一一对应**。下列字段交付标 **是**，但 **JSON 层暂未 enforce 非空**（quality-gates 定稿后再与 rule 表对齐）：


| 字段                        | 说明                                             |
| ------------------------- | ---------------------------------------------- |
| `summary`                 | 交付须有摘要；JSON 校验仅在与 spec `scope_out` 交叉时引用       |
| `design_goals`            | 人读侧「设计目标」必填；**DES-035** JSON 非空                |
| `file_plan`               | 建议非空；空数组时 path 一致性不检                           |
| `architecture.code_delta` | 人读附录 D 数据源；greenfield 可 `{ "summary": "空仓库" }` |




### 元数据


| 字段                    | 是否必填 | 类型       | 说明 · 如何填                               |
| --------------------- | ---- | -------- | -------------------------------------- |
| `version`             | 是    | `"1"`    | 固定 `"1"`                               |
| `spec_ref`            | 是    | string   | 与上游 `prd.json` **的** `title`（或任务标识）一致 |
| `revision`            | 是    | integer  | 设计环修订，从 1 起；重出设计时递增                    |
| `supersedes_revision` | 否    | integer? | 上一轮 `revision`                         |
| `status`              | 否    | enum?    | `draft`                                |




### 正文


| 字段                        | 是否必填 | 类型                      | 说明 · 如何填                                                                                                                 |
| ------------------------- | ---- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `summary`                 | 是    | string?                 | 一两句设计摘要；宜呼应 `prd.json` 的 `summary`（见上表：JSON 暂未 enforce）                                                                 |
| `background`              | 否    | string?                 | 相对 spec 的额外背景；无则省略                                                                                                       |
| `context_view`            | 是    | ContextView             | 参与者/边界；至少 `actors[]`                                                                                                     |
| `design_goals`            | 是    | string[]                | 可验证目标；引用上游 `FEAT-*` / `US-*` / `REQ-*` id（见上表：JSON 暂未 enforce）                                                           |
| `non_goals`               | 是    | string[]                | 与 `prd.json` 的 `scope_out[]` 对齐                                                                                         |
| `architecture`            | 是    | ArchitectureOverview    | 至少 `solution_strategy`                                                                                                   |
| `modules`                 | 是    | ModuleSpec[]            | 每模块含 `name`、`path`、`responsibility`、`code_domain`                                                                        |
| `external_dependencies`   | 是    | ExternalDependency[]    | 无中间件时显式 `kind=none` 或 `filesystem`                                                                                       |
| `interfaces`              | 是    | InterfaceSpec[]         | 顶层数组；每模块至少一条 `module_ref`（`code_domain=SYS` 模块豁免，见 [design-validate DES-032](../quality-gates/design-validate.md#16-接口)） |
| `data_model`              | 否    | DataEntity[]            | 有持久化/结构化存储时**须填**                                                                                                        |
| `table_schemas`           | 否    | TableSchema[]           | 有表/文件项/Redis/MQ schema 时**须填**；无持久化 CLI 可为 `[]`                                                                          |
| `transaction_constraints` | 否    | TransactionConstraint[] | 多写者/跨存储、spec 一致性非 trivial 时**须填**                                                                                        |
| `error_catalog`           | 是    | ErrorCatalogItem[]      | 全局 `ERR-*`；与接口/用例联动                                                                                                      |
| `non_functional`          | 否    | NfrSpec[]?              | `prd.json` 的 `operational_profile` 有设计侧量化增量时**须填**                                                                      |
| `test_cases`              | 是    | TestCase[]              | 含 `happy` / `negative` / `boundary`；`covers` 宜含 `AC-*`；PRD 有 `SEM-*` 时宜含对应 id 并填 `semantic_evidence`（见 [§semantic_evidence](#semantic_evidence)）                         |




### 附录字段


| 字段             | 是否必填 | 类型             | 说明 · 如何填                                                        |
| -------------- | ---- | -------------- | --------------------------------------------------------------- |
| `traceability` | 是    | TraceRow[]     | `spec_ref_id` + `spec_ref_kind`（`FEAT`/`US`/`AC`）→ `design_ref` |
| `file_plan`    | 是    | FilePlanItem[] | 附录 B；`path` 须与某 `dev_tasks[].path` **完全相同**（**DES-104**；空数组不检 path） |
| `dev_tasks`    | 是    | DevTask[]      | 附录 C **执行计划**；见 [dev_tasks[]](#dev_tasks执行计划) |




### 图与路由


| 字段           | 是否必填 | 类型           | 说明 · 如何填                                                    |
| ------------ | ---- | ------------ | ----------------------------------------------------------- |
| `diagrams`   | 否    | DiagramRef[] | 无持久化、线性 CLI 可为 `[]`；有拓扑/流程时**须填**；见 [diagrams[]](#diagrams) |
| `hitl_flags` | 否    | string[]     | 需人工介入时填；默认 `[]`                                             |




### 辅助字段（canonical 落点）

顶层别名合并见 [JSON 归一化（coerce）](#json-归一化coerce)。


| Canonical 路径                  | 是否必填 | 类型            | 说明 · 如何填                                                       |
| ----------------------------- | ---- | ------------- | -------------------------------------------------------------- |
| `architecture.decisions`      | 否    | AdrItem[]     | 方案对比；评审/HITL 消费，不进人读专章                                         |
| `architecture.code_delta`     | 是    | CodeDelta?    | 人读附录 D 数据源；**DES-036** 要求 `summary` 非空（greenfield 可「空仓库」） |
| `cross_cutting`               | 是    | object?       | 横切键值；**须存在**（可为 `{}`）                                          |
| `cross_cutting.test_strategy` | 否    | TestStrategy? | 与 `test_cases` 互补；人读侧不设专章（templates 映射至测试用例表）                  |
| `notes`                       | 否    | string?       | 自由备注；风险/待办宜写此处或并入相关字段，**勿**单独扩 `open_items` / `risks` 键（当前未建模） |


---



## 标识符约定

`ERR-*`、`TC-*` 与模块 `code_domain` 共用域前缀注册表（以 `modules[].code_domain` 为主；`external_dependencies` 仅在无封装模块时补充域）。


| 种类   | 格式                 | 说明                                                                                                        |
| ---- | ------------------ | --------------------------------------------------------------------------------------------------------- |
| 错误码  | `ERR-{域}-{序号}`     | `{域}`=责任方大写缩写 2～12 字符；`{序号}`=三位数字，从 001 起；正则见 [DES-023](../quality-gates/design-validate.md#15-错误目录与测试用例) |
| 测试用例 | `TC-{种类}-{域}-{序号}` | `{种类}`=`HAP`                                                                                              |
| 事务   | `TX-{域}-{序号}`      | 可选，用于 `transaction_constraints[].id`                                                                      |


**联动：** `OperationSpec.errors[]` 与 `error_catalog[].code` 一致；`TestCase.error_code`（NEG）须引用已定义的 `ERR-`*；`TestCase.covers[]` 宜含上游 `US-`* / `AC-*` / `SEM-*`（当 [prd.json](./prd-spec.md#semantic_constraints) 声明语义约束时）。`error_catalog[].when` / `message` 宜描述语义违规而非单一示例字面量（**DES-S02**）。

`code_domain`**：** 每模块唯一；字面量 `SYS` 表示横切/基础设施模块，**DES-032** 下可无对应 `interfaces[]` 条目；`ExternalDependency.code_domain` 在 `kind≠none` 时必填，且非 `filesystem` 依赖须使用独立域（与封装模块域不重复）。

---



## diagrams[]

**DiagramRef：** `{ "path", "kind", "title"? }`


| `kind`       | 用途                    |
| ------------ | --------------------- |
| `context`    | 系统/模块拓扑               |
| `sequence`   | 时序                    |
| `flowchart`  | 流程 / 异常分支             |
| `class`      | 类图（少用）                |
| `deployment` | Schema 保留；**Run 不登记** |


`path` 须与 Run 目录落盘的 `*.mmd` 文件名 **完全一致**。同一文件可登记多条（不同 `kind` / `title`）。

**数量（契约层）：** 无持久化、未登记 `diagrams[]` 时可为 `[]`。下列任一成立时 **DES-017**（[design-validate](../quality-gates/design-validate.md#14-图diagrams)）要求同时含 `kind=sequence` 与 `kind=flowchart`（可同文件多段）：spec `context.storage` 持久化；或 `diagrams[]` 已登记任一条（含仅 `context`）。多模块拓扑另宜 `kind=context`（**DES-223**，warn）。

---



## 嵌套类型

**ContextView：** `{ "actors": string[], "external_systems"?: (ExternalSystemRef | string)[], "boundaries"?: string[], "notes"?: string }`

**ExternalSystemRef：** `{ "name", "description"?, "kind"?: string }`

**DataEntity：** `{ "name", "description"?, "storage"?, "fields"?: FieldDef[], "notes"?: string }` — `storage` 与 `table_schemas[].storage` 对齐；`fields` 为逻辑字段（非 DB 列时可选）

**FieldDef：** `{ "name", "type", "required"?: boolean, "description"?, "notes"?: string }`

**ExternalDependency：** `{ "name", "kind", "code_domain"?, "technology"?, "purpose", "endpoint"?, "criticality"?: "required"|"optional", "failure_behavior"?: string }`

**ModuleSpec：** `{ "name", "path", "responsibility", "code_domain", "depends_on"?: string[] }` — `path` 为模块 **主实现文件**（相对 `code_root`）；宜与 `dev_tasks[].path` / `file_plan[].path` 对齐；布局随 Profile（见 [dev_tasks[]](#dev_tasks执行计划)）

**InterfaceSpec：** `{ "name", "module_ref", "file", "protocol", "description"?, "operations": OperationSpec[] }` — `module_ref` 须匹配 `modules[].name`

**OperationSpec：** `{ "name", "summary", "description"?, "inputs": ParamSpec[], "outputs": ParamSpec[], "errors"?: string[], "http"?, "idempotent"?, "notes"? }`

**ParamSpec：** `{ "name", "type", "required": boolean, "description", "default"?, "schema_ref"? }` — `schema_ref` → `data_model[].name`

`protocol`**：** `internal` | `cli` | `http` | `grpc` | `websocket`

`kind`**（ExternalDependency）：** `db` | `cache` | `mq` | `rpc` | `api` | `filesystem` | `blockchain` | `none`

**TableSchema：** `{ "name", "storage", "columns": ColumnDef[], "indexes": IndexDef[], "audit_policy"?: AuditPolicy, "notes"?: string }`

**ColumnDef（必填）：** `{ "name", "type", "nullable": boolean, "description": string, "pk"?: boolean, "unique"?: boolean }`

**IndexDef：** `{ "name", "columns": string[], "unique"?: boolean, "type"?: string, "purpose": string }`

**AuditPolicy：** `{ "require_created_at"?: boolean, "require_updated_at"?: boolean, "require_version"?: boolean, "notes"?: string }`

**TransactionConstraint：** `{ "id", "scope", "boundary", "isolation"?, "idempotency"?, "consistency_ref"?, "notes"?: string }` — `consistency_ref` 可引用上游 spec `consistency_profile` 档位

**ErrorCatalogItem：** `{ "code", "message"?, "when"?, "retryable"?, "recovery"? }` — `recovery` 为对用户/调用方的恢复动作（如 `exit 2`）

**ArchitectureOverview：** `{ "solution_strategy", "style"?, "decisions"?: AdrItem[], "code_delta"?: CodeDelta }`

**AdrItem：** `{ "id"?, "option", "decision", "rationale"? }` — `decision`：`accepted` | `rejected` | `deferred`

**CodeDelta：** `{ "summary", "baseline_ref"?, "notes"? }`

**FilePlanItem：** `{ "path", "action", "reason"? }` — `action`：`create` | `modify` | `delete`

**DevTask：** `{ "id", "path", "description", "depends_on"?: string[], "covers"?: string[] }` — 执行计划一步；`path` 全局唯一（**DES-003**）；`depends_on` 为步骤 id 列表（**DES-004** / **DES-005**）；`covers` 宜含 `AC-*`。细则见 [dev_tasks[]](#dev_tasks执行计划)

**SemanticEvidence：** `{ "constraint_ref", "equivalence_class"?, "proves_dimensions"? }` — 引用 `prd.json` 中 `semantic_constraints[].id`

**TestCase：** `{ "id", "kind", "title"?, "description"?, "steps"?, "expected"?, "covers"?, "error_code"?, "semantic_evidence"? }` — `kind`**：** `happy` | `negative` | `boundary`（与 id 中 HAP/NEG/BND 对应）；`description` 对 `input_shape` happy TC 宜含 `input:` 或 `request:` 前缀（**DES-S05**）

**TraceRow：** `{ "spec_ref_id", "spec_ref_kind", "design_ref" }` — `spec_ref_kind` 如 `FEAT` / `US` / `AC`；宜使用 canonical 键名（勿用旧键 `feature_id`）

**NfrSpec：** `{ "id"?, "metric", "target", "verification"?, "notes"?: string }`

**TestStrategy：** `{ "approach", "paths"?: string[], "notes"?: string }`

---

## dev_tasks[]（执行计划）

人读 **附录 C. 执行计划**（[artifact-templates/design-spec.md](../artifact-templates/design-spec.md) §附录 C）；机器字段 `dev_tasks[]`。

| 项 | 说明 |
|----|------|
| **定位** | 实现 **执行计划**：拓扑有序步骤表；供 [developer-task-batch-spec.md](../developer-task-batch-spec.md) 调度 Developer（task-batch 未启用时仍作 LLM 参考与校验） |
| **一步** | 每条 `DevTask` = 可独立执行的一步；`path` = 该步 **主实现文件**（非功能 epic 名） |
| **语言无关** | 规则适用于全部 Profile；**具体路径**由 Run Profile + [dev-principles-spec.md §1](../artifact-templates/dev-principles-spec.md#1-必备项目文件) 决定 |

### 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 步骤 id，如 `T1`；全局唯一（**DES-002**） |
| `path` | string | 是 | 主实现文件，相对 `code_root`；**每条唯一**（**DES-003**）；宜取自 `modules[].path` 或 `file_plan[]`，不新造 |
| `description` | string | 是 | 本步实现内容（中文）；宜与对应模块 `responsibility` 一致 |
| `depends_on` | string[] | 否 | 必须先完成的 **步骤 id**；默认 `[]` 表示无前置（仅 T1 框架步） |
| `covers` | string[] | 否 | 宜引用 `acceptance_criteria[].id`（`AC-*`）；P0 追溯见 **DES-009** / **DES-101** |

### T1 框架步（`depends_on` 为空的首步）

首步 `path` = 当前 Profile **依赖清单 / 工程根**；业务步 `depends_on` 宜含 `T1`。


| Profile | `path` 示例 |
|---------|-------------|
| `python` | `pyproject.toml` |
| `go` | `go.mod` |
| `java` | `pom.xml` / `build.gradle.kts` |
| `rust` | `Cargo.toml` |
| `solidity` | `foundry.toml` |

测试文件 `path` 宜符合 Profile.`toolchain.test_dir_glob`（[profiles.md](../profiles.md)）。

### 与 `file_plan` / `modules`

| 关系 | 规则 |
|------|------|
| `modules[].path` | 架构阶段确定的主文件；`dev_tasks[].path` **引用**此处或 `file_plan`，不另起布局 |
| `file_plan[]` | 每个 `path` 须 **等于** 某 `dev_tasks[].path`（**DES-104**） |
| 辅助文件 | 仅随主文件创建的占位（包 `__init__`、空 `mod.rs` 等）宜写在 `description`，**不**单独列入 `file_plan`，除非该文件为某步 `path` |

### JSON 校验（design_validate）

| 规则 | 说明 |
|------|------|
| **DES-001** | `dev_tasks` 非空 |
| **DES-002** | `id` 唯一 |
| **DES-003** | `path` 唯一；`id` / `path` / `description` 非空 |
| **DES-004** | `depends_on[]` 引用已存在的 `id` |
| **DES-005** | `depends_on` 无环 |
| **DES-104** | `file_plan[].path` ∈ `{ dev_tasks[].path }` |

体积预算与多微服务拆步见 `artifact-templates/` 附录 C 与 [developer-task-batch-spec.md §5.4](../developer-task-batch-spec.md#54-体积预算常量与估算)（契约层 **不**单独 enforce）。

### 示例片段（`python` Profile）

```json
"file_plan": [
  { "path": "pyproject.toml", "action": "create", "reason": "REQ-0" },
  { "path": "src/parser.py", "action": "create", "reason": "REQ-1" },
  { "path": "tests/test_calc.py", "action": "create", "reason": "AC-1" }
],
"dev_tasks": [
  { "id": "T1", "path": "pyproject.toml", "description": "项目框架搭建", "depends_on": [], "covers": [] },
  { "id": "T2", "path": "src/parser.py", "description": "解析器实现", "depends_on": ["T1"], "covers": ["FEAT-1"] },
  { "id": "T3", "path": "tests/test_calc.py", "description": "自动化测试", "depends_on": ["T2"], "covers": ["AC-1"] }
]
```

---

## semantic_evidence

当 Run `prd.json` 含非空 `semantic_constraints` 时，Architect 在 `test_cases[]` 中提供可机器检查的证据链。校验见 [design-validate §1.7](../quality-gates/design-validate.md#17-语义校验des-s01s05)。

### SemanticEvidence

| 字段 | 类型 | 说明 |
|------|------|------|
| `constraint_ref` | string | 引用 `SEM-*` id |
| `equivalence_class` | string? | 同一约束下的句法变体标识（非 TC id） |
| `proves_dimensions` | string[] | 本 TC 证明哪些 `dimensions` 键 |

### TestCase 扩展字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `description` | string? | 可解析字面量；`input_shape` happy TC 须 `input: "..."` 或 `request: {...}` |
| `semantic_evidence` | SemanticEvidence? | PRD 有对应 `SEM-*` 时应填 |

**按 PRD `kind` 分支（DES-S01）：**

| PRD `kind` | 要求 |
|------------|------|
| `input_shape` | ≥2 条 happy TC，`equivalence_class` 不同；`proves_dimensions` 并集 = 该 constraint 的 `dimensions` 键 |
| `input_shape` + `one_of:` | 每个枚举值在 happy TC `description` 中至少出现一次（DES-S01b） |
| `invariant` | ≥1 happy/boundary + ≥1 negative |
| `state_transition` | ≥1 TC 且 `steps` 非空 |
| `output_shape` | ≥1 TC 体现输出约束（V1 warn） |

PRD `excludes[]` 非空时，每条 exclude 须有对应 negative TC（DES-S03）。

```json
"test_cases": [
  {
    "id": "TC-HAP-CALC-008",
    "kind": "happy",
    "title": "乘法紧凑写法",
    "description": "input: \"7*8\"",
    "expected": "56",
    "covers": ["AC-1", "REQ-3", "SEM-IN-1"],
    "semantic_evidence": {
      "constraint_ref": "SEM-IN-1",
      "equivalence_class": "multiply-compact",
      "proves_dimensions": ["operand_count", "operator_count", "operator_set"]
    }
  },
  {
    "id": "TC-HAP-CALC-009",
    "kind": "happy",
    "title": "乘法空格写法",
    "description": "input: \"7 * 8\"",
    "expected": "56",
    "covers": ["AC-1", "REQ-3", "SEM-IN-1"],
    "semantic_evidence": {
      "constraint_ref": "SEM-IN-1",
      "equivalence_class": "multiply-spaced",
      "proves_dimensions": ["operand_count", "operator_count", "operator_set"]
    }
  }
]
```

---

## 示例 — default Profile（CLI Todo）

完整 JSON 见仓库 `tests/fixtures/design-todo-valid.json`（与 default Profile Todo 对齐）。

**结构要点（非完整 payload）：**

```json
{
  "version": "1",
  "spec_ref": "CLI Todo App",
  "revision": 1,
  "summary": "CLI Todo 增删查与 JSON 持久化。",
  "context_view": { "actors": ["User", "TodoCLI", "TodoStore"] },
  "architecture": {
    "solution_strategy": "CLI + JSON Store",
    "code_delta": { "summary": "空仓库" }
  },
  "modules": [{ "name": "TodoCLI", "path": "src/cli.py", "responsibility": "…", "code_domain": "CLI" }],
  "external_dependencies": [{ "name": "todos.json", "kind": "filesystem", "purpose": "持久化" }],
  "interfaces": [{ "module_ref": "TodoCLI", "protocol": "cli", "operations": ["…"] }],
  "error_catalog": [{ "code": "ERR-CLI-001", "when": "…", "recovery": "exit 2" }],
  "cross_cutting": { "test_strategy": { "approach": "pytest", "paths": ["tests/test_todo.py"] } },
  "test_cases": [{ "id": "TC-HAP-CLI-001", "kind": "happy", "covers": ["AC-1"] }],
  "traceability": [{ "spec_ref_id": "FEAT-1", "spec_ref_kind": "FEAT", "design_ref": "TodoCLI" }],
  "file_plan": [
    { "path": "pyproject.toml", "action": "create" },
    { "path": "src/todo_store.py", "action": "create" },
    { "path": "src/cli.py", "action": "create" }
  ],
  "dev_tasks": [
    { "id": "T1", "path": "pyproject.toml", "description": "项目框架搭建", "depends_on": [] },
    { "id": "T2", "path": "src/todo_store.py", "description": "JSON 持久化存储", "depends_on": ["T1"], "covers": ["AC-1"] },
    { "id": "T3", "path": "src/cli.py", "description": "CLI 入口", "depends_on": ["T1", "T2"], "covers": ["AC-1"] }
  ]
}
```

