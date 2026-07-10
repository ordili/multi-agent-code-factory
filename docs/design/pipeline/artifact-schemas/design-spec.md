# design-spec.md — DesignArtifact（Architect JSON 契约）

## 依赖上游文档（只读）

审查 / 修订本文时 **以本表、正文字段定义及同名上游人读 § 映射为准**。`quality-gates/` 为**下游**，不在此表列出（见 [README.md §单向依赖](../README.md#1-单向依赖)）。


| 分类            | 上游文档                                                                | 定位                                        |
| ------------- | ------------------------------------------------------------------- | ----------------------------------------- |
| **总设计**       | [multi-agent-pipeline-design.md](../multi-agent-pipeline-design.md) | 系统的总体设计书                                  |
| **上游 JSON 契约** | [prd-spec.md](./prd-spec.md)                                        | 上游 JSON 契约 prd-spec.md（Run `spec.json`） |
| **人读模板**      | [artifact-templates/design-spec.md](../artifact-templates/design-spec.md) | 上游人读 design-spec.md                       |
| **运行配置**      | [profiles.md](../profiles.md)                                       | Profile 注入相关字段语境                            |


---

> **实现：** `multi_agent_code_factory/schemas/design.py`  
> **Run 落盘：** `docs/runs/<task_id>/design.json`  
> **上游 Run：** 同目录 `spec.json`（字段定义见 [prd-spec.md](./prd-spec.md)）

机器可读契约以 **本文 + Pydantic** 为准。

---

## 文档角色

| 项 | 说明 |
|----|------|
| **定义对象** | 单次 Run 的 **`design.json`**（Architect 结构化输出），不是规范文件名本身 |
| **键名** | 英文 snake_case / 枚举字面量（给 Structured Output、校验器、下游 Agent） |
| **字符串值** | **宜中文**（摘要、说明、场景等）；标识符与路径保持英文（见 [语言约定](#语言约定)） |
| **不定义** | Run `design.md` 章节、写作篇幅、Profile 选用（姊妹目录 `artifact-templates/` 规定） |

**数据流：** PM 产出 `spec.json` → Architect 读 `spec.json` 产出 **`design.json`** → 渲染 `design.md` / 登记 `*.mmd`。下游 Developer / QA **以 JSON 为准**。

---

## 语言约定

| 部分 | 语言 | 示例 |
|------|------|------|
| JSON **键** | 英文 | `modules`、`test_cases` |
| **标识符** | 英文 | `FEAT-1`、`ERR-CLI-001`、`TC-HAP-CLI-001` |
| **代码路径** | 英文 | `src/cli.py` |
| **说明类字符串值** | 中文 | `summary`、`error_catalog[].when` |
| Run **`design.md` 正文** | 中文 | 由渲染器自 JSON 生成；人读格式见 `artifact-templates/` 同名 spec |

---

## Pydantic 结构必填

下列键 **缺则 `DesignArtifact.model_validate` 失败**（`coerce_design_payload` 可补 `version` / `revision`；其余键有默认值或可为 `null` / `[]`）：

| 字段 | 类型 | 默认 |
|------|------|------|
| `version` | `"1"` | coerce 可补 `"1"` |
| `spec_ref` | string | 无 |
| `revision` | integer ≥ 1 | coerce 可补 `1` |

---

## JSON 归一化（coerce）

实现：`schemas/design.py` 中 `coerce_design_payload`（Pydantic `before` validator）。在解析 JSON 时 **就地** 修正常见 LLM 形状，**不改变** 字段语义：

| 行为 | 说明 |
|------|------|
| 顶层别名合并 | `decisions` → `architecture.decisions`；`code_delta` → `architecture.code_delta`；`test_strategy` → `cross_cutting.test_strategy` |
| 缺省元数据 | 无 `version` / `revision` 时补 `"1"` / `1` |
| 列表字段 | `modules`、`interfaces` 等：标量或单对象 → 包成数组 |
| 字符串列表 | `design_goals`、`non_goals`、`hitl_flags`：单字符串 → 单元素数组 |
| `error_catalog[]` | 项内 `error_code` → `code` |
| `non_functional` | 单对象 → 单元素数组 |
| `diagrams[].kind` | 别名归一（如 `sequence diagram` → `sequence`） |

---

## 字段

**「是否必填」列：**

| 值 | 含义 |
|----|------|
| **是** | 规范交付 intent：须写出实质内容；空 `[]` / `{}` / 空字符串不算完成（说明列例外除外） |
| **否** | 可不写字段；或说明列写明无相关场景时 `[]` / 省略可接受 |

缺键即 Pydantic 报错的字段见 [Pydantic 结构必填](#pydantic-结构必填)。

**与校验层的关系：** 「是否必填」表达 **交付 intent**（与人读 `design.md` 的 JSON 映射一致，映射表在 `artifact-templates/` 同名 spec）。与当前 JSON 校验 **不完全一一对应**。下列字段交付标 **是**，但 **JSON 层暂未 enforce 非空**（quality-gates 定稿后再与 rule 表对齐）：

| 字段 | 说明 |
|------|------|
| `summary` | 交付须有摘要；JSON 校验仅在与 spec `scope_out` 交叉时引用 |
| `design_goals` | 人读侧「设计目标」必填；JSON 层暂未 enforce 非空 |
| `file_plan` | 建议非空；空数组时 path 一致性不检 |
| `architecture.code_delta` | 人读附录 D 数据源；greenfield 可 `{ "summary": "空仓库" }` |

### 元数据

| 字段 | 是否必填 | 类型 | 说明 · 如何填 |
|------|----------|------|----------------|
| `version` | 是 | `"1"` | 固定 `"1"` |
| `spec_ref` | 是 | string | 与上游 **`spec.json` 的 `title`**（或任务标识）一致 |
| `revision` | 是 | integer | 设计环修订，从 1 起；重出设计时递增 |
| `supersedes_revision` | 否 | integer? | 上一轮 `revision` |
| `status` | 否 | enum? | `draft` \| `in-review` \| `approved` |

### 正文

| 字段 | 是否必填 | 类型 | 说明 · 如何填 |
|------|----------|------|----------------|
| `summary` | 是 | string? | 一两句设计摘要；宜呼应 `spec.json` 的 `summary`（见上表：JSON 暂未 enforce） |
| `background` | 否 | string? | 相对 spec 的额外背景；无则省略 |
| `context_view` | 是 | ContextView | 参与者/边界；至少 `actors[]` |
| `design_goals` | 是 | string[] | 可验证目标；引用上游 `FEAT-*` / `US-*` / `REQ-*` id（见上表：JSON 暂未 enforce） |
| `non_goals` | 是 | string[] | 与 `spec.json` 的 `scope_out[]` 对齐 |
| `architecture` | 是 | ArchitectureOverview | 至少 `solution_strategy` |
| `modules` | 是 | ModuleSpec[] | 每模块含 `name`、`path`、`responsibility`、`code_domain` |
| `external_dependencies` | 是 | ExternalDependency[] | 无中间件时显式 `kind=none` 或 `filesystem` |
| `interfaces` | 是 | InterfaceSpec[] | 顶层数组；每模块至少一条 `module_ref`（`code_domain=SYS` 模块豁免，见 [design-validate DES-032](../quality-gates/design-validate.md#16-接口)） |
| `data_model` | 否 | DataEntity[] | 有持久化/结构化存储时**须填** |
| `table_schemas` | 否 | TableSchema[] | 有表/文件项/Redis/MQ schema 时**须填**；无持久化 CLI 可为 `[]` |
| `transaction_constraints` | 否 | TransactionConstraint[] | 多写者/跨存储、spec 一致性非 trivial 时**须填** |
| `error_catalog` | 是 | ErrorCatalogItem[] | 全局 `ERR-*`；与接口/用例联动 |
| `non_functional` | 否 | NfrSpec[]? | `spec.json` 的 `operational_profile` 有设计侧量化增量时**须填** |
| `test_cases` | 是 | TestCase[] | 含 `happy` / `negative` / `boundary`；`covers` 宜含 `AC-*` |

### 附录字段

| 字段 | 是否必填 | 类型 | 说明 · 如何填 |
|------|----------|------|----------------|
| `traceability` | 是 | TraceRow[] | `spec_ref_id` + `spec_ref_kind`（`FEAT`/`US`/`AC`）→ `design_ref` |
| `file_plan` | 是 | FilePlanItem[] | 路径与 `dev_tasks[].path` / 模块 `path` 一致（见上表：空数组不检 path） |
| `dev_tasks` | 是 | DevTask[] | `covers[]` 宜引用上游 `acceptance_criteria[].id` |

### 图与路由

| 字段 | 是否必填 | 类型 | 说明 · 如何填 |
|------|----------|------|----------------|
| `diagrams` | 否 | DiagramRef[] | 无持久化、线性 CLI 可为 `[]`；有拓扑/流程时**须填**；见 [diagrams[]](#diagrams) |
| `hitl_flags` | 否 | string[] | 需人工介入时填；默认 `[]` |

### 辅助字段（canonical 落点）

顶层别名合并见 [JSON 归一化（coerce）](#json-归一化coerce)。

| Canonical 路径 | 是否必填 | 类型 | 说明 · 如何填 |
|----------------|----------|------|----------------|
| `architecture.decisions` | 否 | AdrItem[] | 方案对比；评审/HITL 消费，不进人读专章 |
| `architecture.code_delta` | 是 | CodeDelta? | 人读附录 D 数据源；与现有代码库差异摘要（见上表） |
| `cross_cutting` | 是 | object? | 横切键值；**须存在**（可为 `{}`） |
| `cross_cutting.test_strategy` | 否 | TestStrategy? | 与 `test_cases` 互补；人读侧不设专章（templates 映射至测试用例表） |
| `notes` | 否 | string? | 自由备注；风险/待办宜写此处或并入相关字段，**勿**单独扩 `open_items` / `risks` 键（当前未建模） |

---

## 标识符约定

`ERR-*`、`TC-*` 与模块 **`code_domain`** 共用域前缀注册表（以 `modules[].code_domain` 为主；`external_dependencies` 仅在无封装模块时补充域）。

| 种类 | 格式 | 说明 |
|------|------|------|
| 错误码 | `ERR-{域}-{序号}` | `{域}`=责任方大写缩写 2～12 字符；`{序号}`=三位数字，从 001 起；正则见 [DES-023](../quality-gates/design-validate.md#15-错误目录与测试用例) |
| 测试用例 | `TC-{种类}-{域}-{序号}` | `{种类}`=`HAP` \| `NEG` \| `BND`；正则 `^TC-(HAP\|NEG\|BND)-[A-Z][A-Z0-9_]{1,11}-\d{3}$`（**DES-024**） |
| 事务 | `TX-{域}-{序号}` | 可选，用于 `transaction_constraints[].id` |

**联动：** `OperationSpec.errors[]` 与 `error_catalog[].code` 一致；`TestCase.error_code`（NEG）须引用已定义的 `ERR-*`；`TestCase.covers[]` 宜含上游 `US-*` / `AC-*`。

**`code_domain`：** 每模块唯一；字面量 **`SYS`** 表示横切/基础设施模块，**DES-032** 下可无对应 `interfaces[]` 条目；`ExternalDependency.code_domain` 在 `kind≠none` 时必填，且非 `filesystem` 依赖须使用独立域（与封装模块域不重复）。

---

## diagrams[]

**DiagramRef：** `{ "path", "kind", "title"? }`

| `kind` | 用途 |
|--------|------|
| `context` | 系统/模块拓扑 |
| `sequence` | 时序 |
| `flowchart` | 流程 / 异常分支 |
| `class` | 类图（少用） |
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

**ModuleSpec：** `{ "name", "path", "responsibility", "code_domain", "depends_on"?: string[] }`

**InterfaceSpec：** `{ "name", "module_ref", "file", "protocol", "description"?, "operations": OperationSpec[] }` — `module_ref` 须匹配 `modules[].name`

**OperationSpec：** `{ "name", "summary", "description"?, "inputs": ParamSpec[], "outputs": ParamSpec[], "errors"?: string[], "http"?, "idempotent"?, "notes"? }`

**ParamSpec：** `{ "name", "type", "required": boolean, "description", "default"?, "schema_ref"? }` — `schema_ref` → `data_model[].name`

**`protocol`：** `internal` | `cli` | `http` | `grpc` | `websocket`

**`kind`（ExternalDependency）：** `db` | `cache` | `mq` | `rpc` | `api` | `filesystem` | `blockchain` | `none`

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

**DevTask：** `{ "id", "path", "description", "depends_on"?: string[], "covers"?: string[] }` — `covers` 宜含上游 `AC-*`

**TestCase：** `{ "id", "kind", "title"?, "steps"?, "expected"?, "covers"?, "error_code"? }` — **`kind`：** `happy` | `negative` | `boundary`（与 id 中 HAP/NEG/BND 对应，见 [标识符约定](#标识符约定)）

**TraceRow：** `{ "spec_ref_id", "spec_ref_kind", "design_ref" }` — `spec_ref_kind` 如 `FEAT` / `US` / `AC`；宜使用 canonical 键名（勿用旧键 `feature_id`）

**NfrSpec：** `{ "id"?, "metric", "target", "verification"?, "notes"?: string }`

**TestStrategy：** `{ "approach", "paths"?: string[], "notes"?: string }`

---

## 示例 — default Profile（CLI Todo）

完整 JSON 见仓库 **`tests/fixtures/design-todo-valid.json`**（与 default Profile Todo 对齐）。

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
  "dev_tasks": [{ "id": "T1", "path": "src/todo_store.py", "covers": ["AC-1"] }]
}
```
