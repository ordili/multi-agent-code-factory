# DesignArtifact — Architect 输出（JSON）

> **人读基线：** [Google Design Doc](https://google.github.io/eng-practices/) + 七项工程必备 → [artifact-templates/design.md](../artifact-templates/design.md)  
> **实现：** `multi_agent_code_factory/schemas/design.py`  
> **Run 路径：** `design.json`（+ `design.md`、`*.mmd`）  
> **下游：** 须通过 [design_validate](../quality-gates.md#4-design_validate--规则清单)

## 字段

### 元数据

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | `"1"` | Schema 版本 |
| `spec_ref` | string | 对应 spec 标题 / task |
| `revision` | integer | 设计环修订，从 1 起 |
| `supersedes_revision` | integer? | 上一轮 revision |
| `status` | enum? | `draft` \| `in-review` \| `approved` |

### 正文 — Design Doc（§1–§11）

| 字段 | 类型 | § |
|------|------|---|
| `summary` | string? | §1 |
| `background` | string? | §1 |
| `context_view` | ContextView | §1 |
| `design_goals` | string[] | §2 |
| `constraints_ref` | string[]? | §2 |
| `non_goals` | string[] | §3 |
| `architecture` | ArchitectureOverview | §4.1 |
| `modules` | ModuleSpec[] | §4.2 |
| `external_dependencies` | ExternalDependency[] | **§4.3 外部依赖** |
| `interfaces` | InterfaceSpec[] | §4.4 |
| `data_model` | DataEntity[] | §4.5 逻辑模型 |
| `table_schemas` | TableSchema[] | **§4.5 表结构** |
| `decisions` | AdrItem[] | §5 |
| `cross_cutting` | CrossCuttingSpec | §6（安全/配置/观测） |
| `transaction_constraints` | TransactionConstraint[] | **§6.1 事务/一致性** |
| `error_catalog` | ErrorCatalogItem[] | **§6.2 错误码** |
| `non_functional` | NfrSpec[]? | §7 |
| `test_strategy` | TestStrategy | §8 |
| `deployment` | DeploymentSpec? | §9 |
| `rollout` | RolloutSpec? | §9 |
| `monitoring` | MonitoringSpec? | §10 |
| `open_items` | string[]? | §11 |
| `risks` | RiskItem[]? | §11 |

### 附录 — 实现蓝图

| 字段 | 类型 | 附录 |
|------|------|------|
| `traceability` | TraceRow[] | A |
| `file_plan` | FilePlanItem[] | B |
| `dev_tasks` | DevTask[] | C |
| `test_cases` | TestCase[] | **D 测试用例设计** |
| `code_delta` | CodeDelta? | E |

> `test_strategy.paths[]` 与 `test_cases[]` 配套：用例 id → 实现文件。

### 图与标志

| 字段 | 类型 | 说明 |
|------|------|------|
| `diagrams` | DiagramRef[] | **须** 含 `sequence` **与** `flowchart`（§4.6） |
| `hitl_flags` | string[] | HITL |
| `notes` | string? | 补充 |

### 嵌套类型

**ExternalDependency：** `{ "name", "kind", "code_domain"?, "technology"?, "purpose", "endpoint"?, "criticality"?: "required"|"optional", "failure_behavior"?: string }` — **`code_domain` 必填**（**`kind=none` 可省略**）；非 `filesystem` 依赖须独立域（见 [artifact-templates/design.md](../artifact-templates/design.md) §域前缀注册）

**ModuleSpec：** `{ "name", "path", "responsibility", "code_domain", "depends_on"?: string[] }` — **`code_domain` 必填**，模块间唯一

**InterfaceSpec：** `{ "name", "module_ref", "file", "protocol", "description"?, "operations": OperationSpec[] }` — **`module_ref`** 须匹配 `modules[].name`；见 [artifact-templates/design.md](../artifact-templates/design.md) §4.4

**OperationSpec：** `{ "name", "summary", "description"?, "inputs": ParamSpec[], "outputs": ParamSpec[], "errors"?: string[], "http"?, "idempotent"?, "notes"? }`

**ParamSpec：** `{ "name", "type", "required": boolean, "description", "default"?, "schema_ref"? }` — `schema_ref` → `data_model[].name`

**`protocol`：** `internal` | `cli` | `http` | `grpc` | `websocket`

**`kind`：** `db` | `cache` | `mq` | `rpc` | `api` | `filesystem` | `blockchain` | `none`

**TableSchema：** `{ "name", "storage", "columns": ColumnDef[], "indexes": IndexDef[], "audit_policy"?: AuditPolicy, "notes"?: string }`

**ColumnDef（必填）：** `{ "name", "type", "nullable": boolean, "description": string, "pk"?: boolean, "unique"?: boolean }`

**IndexDef：** `{ "name", "columns": string[], "unique"?: boolean, "type"?: string, "purpose": string }`

**AuditPolicy：** `{ "require_created_at"?: boolean, "require_updated_at"?: boolean, "require_version"?: boolean, "notes"?: string }`

**TransactionConstraint：** `{ "id", "scope", "boundary", "isolation"?, "idempotency"?, "consistency_ref"?, "notes"?: string }`

**ErrorCatalogItem：** `{ "code", ... }` — **`code` 必填**，格式 `ERR-{域}-{序号}`（见 artifact-templates/design.md §编码规范）

**TestCase：** `{ "id", "kind", ... "error_code"?: string }` — **`id` 必填**，格式 `TC-{HAP|NEG|BND}-{域}-{序号}`；`error_code` 须为已定义的 `ERR-*`

**ContextView / ArchitectureOverview / DataEntity / CrossCuttingSpec / NfrSpec / AdrItem / RiskItem / TraceRow / FilePlanItem / DevTask / CodeDelta / TestStrategy / RolloutSpec / MonitoringSpec / DiagramRef** — 见 [artifact-templates/design.md](../artifact-templates/design.md)。

**DiagramRef `kind`：** `sequence` | `flowchart` | `class` | `context` | `deployment`

## 示例 — default Profile（CLI Todo）

> **说明：** 与 [`artifact-templates/design.md`](../artifact-templates/design.md) 样例文档一致；Todo 为 **Profile=default** 教学 fixture。长运行 / 多服务类任务见 artifact-templates 正文「多服务」示例（V2 领域见 [domains/](../../../../domains/README.md)）。

```json
{
  "version": "1",
  "spec_ref": "CLI Todo App",
  "revision": 1,
  "summary": "CLI Todo 增删查与 JSON 持久化。",
  "design_goals": ["CRUD 稳定", "持久化可单测"],
  "non_goals": ["Web UI", "多用户"],
  "architecture": { "solution_strategy": "CLI + JSON Store", "style": "layered" },
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
  "cross_cutting": { "configuration": "默认路径 ./todos.json" },
  "test_strategy": { "approach": "pytest", "paths": ["tests/test_todo.py"] },
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
  "decisions": [
    { "id": "ADR-1", "option": "JSON 文件", "decision": "accepted", "rationale": "spec json_file；零依赖" },
    { "id": "ADR-2", "option": "SQLite", "decision": "rejected", "rationale": "超出 scope" }
  ],
  "traceability": [{ "spec_ref_id": "FEAT-1", "spec_ref_kind": "FEAT", "design_ref": "TodoCLI" }],
  "file_plan": [{ "path": "src/cli.py", "action": "create", "reason": "CLI" }],
  "dev_tasks": [{ "id": "T1", "path": "src/cli.py", "description": "子命令", "depends_on": [] }],
  "code_delta": { "summary": "空仓库" },
  "diagrams": [
    { "path": "flow.mmd", "kind": "sequence", "title": "add 命令时序" },
    { "path": "flow.mmd", "kind": "flowchart", "title": "持久化与异常分支" }
  ],
  "hitl_flags": []
}
```

人读章节见 [artifact-templates/design.md](../artifact-templates/design.md)。更多 JSON 片段见 [examples/snippets/](../examples/snippets/)。
