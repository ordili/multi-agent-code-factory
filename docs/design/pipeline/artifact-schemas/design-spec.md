# design-spec.md — DesignArtifact（Architect JSON 契约）

> **实现：** `multi_agent_code_factory/schemas/design.py`  
> **Run 路径：** `docs/runs/<task_id>/design.json`  
> **上游：** [prd-spec.md](./prd-spec.md) → Run `spec.json`（`spec_ref`、`traceability` 中的 `FEAT-*` / `US-*` / `AC-*`、`consistency_profile` 等）

机器可读契约以 **本文 + Pydantic** 为准。**本文不描述**人读格式与下游章节。

---

## 字段

### 元数据

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | `"1"` | Schema 版本 |
| `spec_ref` | string | 对应 [spec.json](./prd-spec.md) 的 `title` 或任务标识 |
| `revision` | integer | 设计环修订，从 1 起 |
| `supersedes_revision` | integer? | 上一轮 revision |
| `status` | enum? | `draft` \| `in-review` \| `approved` |

### 正文

| 字段 | 类型 | 说明 |
|------|------|------|
| `summary` | string? | 设计摘要 |
| `background` | string? | 背景补充 |
| `context_view` | ContextView | 上下文视图（参与者、边界等）；**宜非空** |
| `design_goals` | string[] | 设计目标；宜引用上游 `FEAT-*` / `US-*` / `REQ-*` |
| `non_goals` | string[] | 非目标；与 spec `scope_out` 对齐 |
| `architecture` | ArchitectureOverview | 方案概述；见 [嵌套类型](#嵌套类型)（含 `decisions`、`code_delta`） |
| `modules` | ModuleSpec[] | 模块划分 |
| `external_dependencies` | ExternalDependency[] | 外部依赖 |
| `interfaces` | InterfaceSpec[] | 接口与操作 |
| `data_model` | DataEntity[] | 逻辑数据实体 |
| `table_schemas` | TableSchema[] | 表 / 文件项 / Redis / MQ 等物理结构 |
| `transaction_constraints` | TransactionConstraint[] | 事务与一致性边界 |
| `error_catalog` | ErrorCatalogItem[] | 全局错误码表 |
| `non_functional` | NfrSpec[]? | 非功能性指标（性能、可用性等） |
| `test_cases` | TestCase[] | 测试用例清单 |

### 附录字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `traceability` | TraceRow[] | 上游 spec id → 本设计模块/接口的追溯 |
| `file_plan` | FilePlanItem[] | 计划创建/修改的文件 |
| `dev_tasks` | DevTask[] | 开发任务分解 |

> **`code_delta`（附录 D）：** 写在 **`architecture.code_delta`**，不要与顶层 `architecture` 平级的重复键。

### 图与路由

| 字段 | 类型 | 说明 |
|------|------|------|
| `diagrams` | DiagramRef[] | 配套 Mermaid 文件索引；见 [diagrams[]](#diagrams) |
| `hitl_flags` | string[] | 需人工介入的标志；供 HITL 路由读取 |

### 辅助字段（仅 JSON，无独立人读章节）

下列字段供 Agent、normalizer、HITL 使用；**canonical 落点**如下（normalizer 会将 LLM 误写的顶层同名键 **合并** 到 canonical 路径）。

| Canonical 路径 | 类型 | 说明 |
|----------------|------|------|
| `architecture.decisions` | AdrItem[] | 方案对比与 ADR；评审/HITL 消费 |
| `architecture.code_delta` | CodeDelta? | 与现有代码库差异（附录 D 数据源） |
| `cross_cutting` | object? | 横切配置；**`test_strategy` 嵌套在 `cross_cutting` 内** |
| `cross_cutting.test_strategy` | TestStrategy? | 测试方式与路径；与 `test_cases` 互补 |
| `notes` | string? | 补充说明（Pydantic 已建模） |
| `open_items` / `risks` | item[] | 扩展键；经 `architecture` / `cross_cutting` 传递时可保留 |

---

## 标识符约定

`ERR-*`、`TC-*` 与模块 **`code_domain`** 共用域前缀注册表（以 `modules[].code_domain` 为主；`external_dependencies` 仅在无封装模块时补充域）。

| 种类 | 格式 | 说明 |
|------|------|------|
| 错误码 | `ERR-{域}-{序号}` | `{域}`=责任方大写缩写 2～12 字符；`{序号}`=三位数字，从 001 起 |
| 测试用例 | `TC-{种类}-{域}-{序号}` | `{种类}`=`HAP` \| `NEG` \| `BND` |
| 事务 | `TX-{域}-{序号}` | 可选，用于 `transaction_constraints[].id` |

**联动：** `OperationSpec.errors[]` 与 `error_catalog[].code` 一致；`TestCase.error_code`（NEG）须引用已定义的 `ERR-*`；`TestCase.covers[]` 宜含上游 `US-*` / `AC-*`。

**`code_domain`：** 每模块唯一；`ExternalDependency.code_domain` 在 `kind≠none` 时必填，且非 `filesystem` 依赖须使用独立域（与封装模块域不重复）。

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

**数量（契约层）：** 无持久化的纯 CLI（stateless）且未声明多步流程时，`diagrams` **可为 `[]`**；存在持久化、多模块拓扑或多步业务/数据流时，宜含 `context` 及至少一种 `sequence` / `flowchart`。

---

## 嵌套类型

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

**ErrorCatalogItem：** `{ "code", "message"?, "when"?, "retryable"?, "recovery"? }`

**ArchitectureOverview：** `{ "solution_strategy", "style"?, "decisions"?: AdrItem[], "code_delta"?: CodeDelta }`

**AdrItem：** `{ "id"?, "option", "decision", "rationale"? }` — `decision`：`accepted` \| `rejected` \| `deferred`

**CodeDelta：** `{ "summary", "baseline_ref"?, "notes"? }`

**FilePlanItem：** `{ "path", "action", "reason"? }` — `action`：`create` \| `modify` \| `delete`

**DevTask：** `{ "id", "path", "description", "depends_on"?: string[], "covers"?: string[] }` — `covers` 宜含上游 `AC-*`

**TestCase：** `{ "id", "kind", "title"?, "steps"?, "expected"?, "covers"?, "error_code"? }` — **`kind`：** `happy` \| `negative` \| `boundary`（与 id 中 HAP/NEG/BND 对应，见 [标识符约定](#标识符约定)）

**TraceRow：** `{ "spec_ref_id", "spec_ref_kind", "design_ref" }` — `spec_ref_kind` 如 `FEAT` / `US` / `AC`

**ContextView / DataEntity / NfrSpec / TestStrategy** — 其余字段见 Pydantic `schemas/design.py`。

---

## 示例 — default Profile（CLI Todo）

```json
{
  "version": "1",
  "spec_ref": "CLI Todo App",
  "revision": 1,
  "summary": "CLI Todo 增删查与 JSON 持久化。",
  "design_goals": ["CRUD 稳定", "持久化可单测"],
  "non_goals": ["Web UI", "多用户"],
  "context_view": {
    "actors": ["User", "TodoCLI", "TodoStore"]
  },
  "architecture": {
    "solution_strategy": "CLI + JSON Store",
    "style": "layered",
    "decisions": [
      { "id": "ADR-1", "option": "JSON 文件", "decision": "accepted", "rationale": "spec json_file；零依赖" },
      { "id": "ADR-2", "option": "SQLite", "decision": "rejected", "rationale": "超出 scope" }
    ],
    "code_delta": { "summary": "空仓库 greenfield" }
  },
  "modules": [
    { "name": "TodoCLI", "path": "src/cli.py", "responsibility": "子命令", "code_domain": "CLI" },
    { "name": "TodoStore", "path": "src/todo_store.py", "responsibility": "JSON IO", "code_domain": "STORE" }
  ],
  "external_dependencies": [
    {
      "name": "todos.json",
      "kind": "filesystem",
      "code_domain": "STORE",
      "technology": "local file",
      "purpose": "持久化",
      "criticality": "required",
      "failure_behavior": "不可写则 ERR-STORE-002（域=封装模块 STORE）"
    }
  ],
  "interfaces": [
    {
      "name": "TodoCLI",
      "module_ref": "TodoCLI",
      "file": "src/cli.py",
      "protocol": "cli",
      "description": "命令行子命令入口",
      "operations": [
        {
          "name": "add",
          "summary": "添加待办",
          "inputs": [{ "name": "text", "type": "string", "required": true, "description": "待办正文" }],
          "outputs": [{ "name": "exit_code", "type": "integer", "required": true, "description": "0 成功" }],
          "errors": ["ERR-CLI-001"]
        },
        {
          "name": "list",
          "summary": "列出待办",
          "inputs": [],
          "outputs": [{ "name": "todos", "type": "Todo[]", "required": true, "description": "stdout 输出", "schema_ref": "Todo" }],
          "errors": ["ERR-STORE-001"]
        },
        {
          "name": "done",
          "summary": "标记完成",
          "inputs": [{ "name": "id", "type": "string(uuid)", "required": true, "description": "待办 id" }],
          "outputs": [{ "name": "exit_code", "type": "integer", "required": true, "description": "0 成功" }],
          "errors": ["ERR-CLI-001", "ERR-STORE-002"]
        }
      ]
    },
    {
      "name": "TodoStore",
      "module_ref": "TodoStore",
      "file": "src/todo_store.py",
      "protocol": "internal",
      "description": "JSON 文件持久化",
      "operations": [
        {
          "name": "load",
          "summary": "读取 todos 文件",
          "inputs": [{ "name": "path", "type": "string", "required": false, "description": "默认 ./todos.json" }],
          "outputs": [{ "name": "todos", "type": "Todo[]", "required": true, "description": "解析结果", "schema_ref": "Todo" }],
          "errors": ["ERR-STORE-001"]
        },
        {
          "name": "save",
          "summary": "原子写入全量列表",
          "inputs": [
            { "name": "todos", "type": "Todo[]", "required": true, "description": "全量数据", "schema_ref": "Todo" },
            { "name": "path", "type": "string", "required": false, "description": "目标路径" }
          ],
          "outputs": [],
          "errors": ["ERR-STORE-002"]
        },
        {
          "name": "append",
          "summary": "追加一条并持久化",
          "inputs": [{ "name": "todo", "type": "Todo", "required": true, "description": "新待办", "schema_ref": "Todo" }],
          "outputs": [{ "name": "todo", "type": "Todo", "required": true, "description": "含 id 与时间戳", "schema_ref": "Todo" }],
          "errors": ["ERR-STORE-002"]
        }
      ]
    }
  ],
  "data_model": [{ "name": "Todo", "description": "待办项", "storage": "todos.json" }],
  "table_schemas": [
    {
      "name": "todos (JSON array item)",
      "storage": "todos.json",
      "audit_policy": {
        "require_created_at": true,
        "require_updated_at": true,
        "require_version": false,
        "notes": "实体级 ISO8601；无 DB 索引"
      },
      "columns": [
        { "name": "id", "type": "string(uuid)", "nullable": false, "pk": true, "description": "主键" },
        { "name": "text", "type": "string", "nullable": false, "description": "待办正文" },
        { "name": "done", "type": "boolean", "nullable": false, "description": "是否完成" },
        { "name": "created_at", "type": "string(ISO8601)", "nullable": false, "description": "创建时间" },
        { "name": "updated_at", "type": "string(ISO8601)", "nullable": false, "description": "最后修改时间" }
      ],
      "indexes": [],
      "notes": "personal 规模全量 load；无额外索引"
    }
  ],
  "transaction_constraints": [
    {
      "id": "TX-STORE-001",
      "scope": "save",
      "boundary": "单文件原子写 temp+rename",
      "consistency_ref": "spec local_only"
    }
  ],
  "error_catalog": [
    { "code": "ERR-CLI-001", "message": "Invalid argument", "when": "空标题等参数非法", "retryable": false, "recovery": "exit 2" },
    { "code": "ERR-STORE-001", "message": "Invalid JSON", "when": "load 解析失败", "retryable": false, "recovery": "exit 1" },
    { "code": "ERR-STORE-002", "message": "Write failed", "when": "磁盘不可写", "retryable": true, "recovery": "提示权限" }
  ],
  "cross_cutting": {
    "configuration": "默认路径 ./todos.json",
    "test_strategy": { "approach": "pytest", "paths": ["tests/test_todo.py"] }
  },
  "test_cases": [
    {
      "id": "TC-HAP-CLI-001",
      "kind": "happy",
      "title": "添加待办",
      "steps": ["todo add a", "todo list"],
      "expected": "列表含 a",
      "covers": ["AC-1", "US-1"]
    },
    {
      "id": "TC-HAP-STORE-001",
      "kind": "happy",
      "title": "重启持久化",
      "steps": ["add", "新进程 list"],
      "expected": "数据仍在",
      "covers": ["US-2", "AC-1"]
    },
    {
      "id": "TC-NEG-CLI-001",
      "kind": "negative",
      "title": "空标题",
      "steps": ["todo add ''"],
      "expected": "exit 2 ERR-CLI-001",
      "covers": ["US-1"],
      "error_code": "ERR-CLI-001"
    },
    {
      "id": "TC-NEG-STORE-001",
      "kind": "negative",
      "title": "损坏 JSON",
      "steps": ["非法 JSON 文件", "todo list"],
      "expected": "exit 1 ERR-STORE-001",
      "covers": ["AC-1"],
      "error_code": "ERR-STORE-001"
    },
    {
      "id": "TC-NEG-STORE-002",
      "kind": "negative",
      "title": "磁盘不可写",
      "steps": ["只读目录 add"],
      "expected": "ERR-STORE-002 可重试提示",
      "error_code": "ERR-STORE-002"
    },
    {
      "id": "TC-BND-CLI-001",
      "kind": "boundary",
      "title": "超长标题",
      "steps": ["todo add 501字符"],
      "expected": "截断至 500 或拒绝",
      "covers": ["US-1"]
    }
  ],
  "traceability": [{ "spec_ref_id": "FEAT-1", "spec_ref_kind": "FEAT", "design_ref": "TodoCLI" }],
  "file_plan": [
    { "path": "src/cli.py", "action": "create", "reason": "CLI" },
    { "path": "src/todo_store.py", "action": "create", "reason": "Store" }
  ],
  "dev_tasks": [
    { "id": "T1", "path": "src/todo_store.py", "description": "JSON load/save", "depends_on": [], "covers": ["AC-1"] },
    { "id": "T2", "path": "src/cli.py", "description": "子命令", "depends_on": ["T1"], "covers": ["AC-1"] }
  ],
  "diagrams": [
    { "path": "architecture-todo.mmd", "kind": "context", "title": "Todo 模块拓扑" },
    { "path": "flow-todo.mmd", "kind": "sequence", "title": "add 命令时序" },
    { "path": "flow-todo.mmd", "kind": "flowchart", "title": "持久化与异常分支" }
  ],
  "hitl_flags": []
}
```
