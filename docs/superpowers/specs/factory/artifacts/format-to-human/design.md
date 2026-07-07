# design.md — Design Doc（人读格式）

> **标准基线：** [Google Engineering Practices — Design Docs](https://google.github.io/eng-practices/)  
> **机器真源：** [`../schemas/design.md`](../schemas/design.md)（`DesignArtifact` / `design.json`）  
> **Run 路径：** `docs/factory/runs/<task_id>/design.md`  
> **配套图：** [flow.md](./flow.md) → Run 的 `*.mmd`  
> **校验：** JSON → [quality-gates.md §4](../../quality-gates.md#4-design_validate--规则清单)；MD → §4.3（P1）

---

## 文档定位

| 对比 | spec.md | design.md |
|------|---------|-----------|
| 回答 | 做什么、验收什么 | 怎么做、依赖什么、数据怎么存、异常怎么处理 |
| 读者 | PM、HITL | Architect、Developer、QA、Reviewer |

**正文 §1–§11** = Google 式 Design Doc + **七项工程必备**（外部依赖、**模块 API**、表结构、Flow 图、测试用例、事务一致性、错误码）。  
**附录 A–E** = Agent 流水线实现蓝图。

---

## 固定章节

### 正文

| § | Markdown 标题 | 对应 JSON | 必填 |
|---|---------------|-----------|------|
| — | `# Design Doc — {spec_ref}` | 元数据 | ✓ |
| 1 | `## 1. Context & Background` | `summary`、`background?`、`context_view` | ✓ |
| 2 | `## 2. Goals` | `design_goals[]`、`constraints_ref[]` | ✓ |
| 3 | `## 3. Non-Goals` | `non_goals[]` | ✓ |
| 4 | `## 4. Design` | 见 §4 子节 | ✓ |
| 5 | `## 5. Alternatives Considered` | `decisions[]` | ✓ |
| 6 | `## 6. Cross-cutting Concerns` | `cross_cutting`、`transaction_constraints[]`、`error_catalog[]` | ✓ |
| 7 | `## 7. Performance & Reliability` | `non_functional[]` | 条件* |
| 8 | `## 8. Testing Plan` | `test_strategy` | ✓ |
| 9 | `## 9. Rollout & Deployment` | `deployment`、`rollout?` | 条件* |
| 10 | `## 10. Monitoring & Alerting` | `monitoring?` | 条件* |
| 11 | `## 11. Open Questions` | `open_items[]`、`risks[]` | ✓ |

### §4 Design — 固定子节

| 子节 | 标题 | JSON | 必填 |
|------|------|------|------|
| 4.1 | `### 4.1 Overview` | `architecture` | ✓ |
| 4.2 | `### 4.2 Components` | `modules[]`（含 **`code_domain`**） | ✓ |
| 4.3 | `### 4.3 External Dependencies` | `external_dependencies[]`（含 **`code_domain`**） | ✓ |
| 4.4 | `### 4.4 APIs` | `interfaces[]` → **`operations[]`** | ✓ |
| 4.5 | `### 4.5 Data Model & Table Schema` | `data_model[]`、`table_schemas[]` | ✓ |
| 4.6 | `### 4.6 Flow` | `diagrams[]` → `*.mmd` | ✓ |

\* §7：spec §8 非 trivial 时必填。§9–§10：长运行服务 / deploy Profile 时必填。

### 附录

| 附录 | 标题 | JSON | 必填 |
|------|------|------|------|
| A | `## 附录 A. 需求追溯` | `traceability[]` | ✓ |
| B | `## 附录 B. 文件变更计划` | `file_plan[]` | ✓ |
| C | `## 附录 C. 开发任务分解` | `dev_tasks[]` | ✓ |
| D | `## 附录 D. 测试用例设计` | `test_cases[]` + `test_strategy.paths` | ✓ |
| E | `## 附录 E. 与现有代码对照` | `code_delta` | ✓ |

**页眉（推荐）：** `# Design Doc — {title}` + Revision / Spec / Status / Supersedes

---

## 各节写法

### §1 Context & Background

- **summary**：1–3 句说明本设计解决什么。
- **context_view**：`actors[]`（谁用）、`external_systems[]`（边界上的外部实体，**角色级**）。
- 与 §4.3 分工：§1 不写连接串/版本；§4.3 写可实施依赖。

### §2 Goals / §3 Non-Goals

- **Goals**：可验证目标，引用 spec KPI/约束（`constraints_ref[]`）。
- **Non-Goals**：显式排除项，与 spec `scope_out` 对齐。

### §4.1 Overview

- `architecture.solution_strategy`：一句话架构；`style`（layered / pipeline / …）。
- 可附组件关系一句，细节在 §4.2–§4.4。

### §4.2 Components（模块与 code_domain）

表格推荐：

| 模块 | 路径 | 职责 | **code_domain** | 依赖模块 |
|------|------|------|-----------------|----------|

- **一模块一域**：每个 `modules[]` 须有 **唯一** `code_domain`（大写缩写，2–12 字符）。
- 模块内抛出的错误 → `ERR-{code_domain}-*`；测该模块 → `TC-*-{code_domain}-*`。
- JSON：`modules[]` → `{ "name", "path", "responsibility", "code_domain", "depends_on"?: [] }`

### §4.3 External Dependencies（外部依赖）

回答：**依赖哪些 DB、缓存、消息队列、RPC、第三方 HTTP 等**（无则显式写「无外部中间件」）。

表格推荐：

| 名称 | 类型 | 技术/版本 | 用途 | 连接/端点 | **code_domain** | 关键性 |
|------|------|-----------|------|-----------|-----------------|--------|

**`kind` 枚举：** `db` | `cache` | `mq` | `rpc` | `api` | `filesystem` | `blockchain` | `none`

- **DB**：PostgreSQL、MySQL、SQLite…  
- **Cache**：Redis、Memcached…  
- **其它服务**：内部 gRPC、DEX RPC、Stripe API 等  
- 须说明 **故障时行为**（降级 / 失败 / 重试）— 可与 §6 错误码呼应  
- **`code_domain`（必填，例外见下）**：错误码/测试域前缀（见 [域前缀注册](#域前缀注册模块--外部服务)）
  - **`db`/`cache`/`mq`/`rpc`/`api`/`blockchain`**：独立域，不得与模块或其它非 `filesystem` 依赖重复（`DES-028`）
  - **`filesystem`**：须 **等于** 封装该 IO 的某模块 `code_domain`（如 `todos.json`→`STORE`）
  - **`none`**（无外部中间件占位）：**省略** `code_domain`（`DES-028`）

JSON：`external_dependencies[]` → `{ "name", "kind", "code_domain"?, "technology"?, "purpose", "endpoint"?, "criticality"?: "required"|"optional", "failure_behavior"? }`

与 §1 `context_view.external_systems` 分工：**Context** 写边界与角色；**§4.3** 写 **可连接、可版本化** 的依赖清单。

### §4.4 APIs（模块 API 定义）

回答：**每个模块对外暴露什么能力**——操作名、功能说明、**入参**、**出参**、可能抛出的错误码。Developer 应能据此写签名与单测，无需猜。

**须覆盖：** `modules[]` 中每个模块至少 1 条 `interfaces[]`（`module_ref` 指向模块名）。

#### 人读格式（每个模块一小节）

```markdown
#### {模块名}（`{文件}` · `{protocol}` · `{code_domain}`）

| 操作 | 功能说明 | 入参 | 出参 | 错误码 |
|------|----------|------|------|--------|
```

- **入参 / 出参**：写 **名称、类型、必填、说明**；复杂类型引用 §4.5 实体（如 `Todo`、`Todo[]`）。
- **错误码**：本操作可能返回/抛出的 `ERR-*`（含透传的上游码）；无则 `—`。
- **HTTP/gRPC**：另写 `method`+`path` 或 proto service；body 映射到入参/出参表。
- **CLI**：子命令即 `operations[].name`；位置参数 / flags 写入参表。

#### JSON — `InterfaceSpec`

```json
{
  "name": "TodoStore",
  "module_ref": "TodoStore",
  "file": "src/todo_store.py",
  "protocol": "internal",
  "description": "JSON 文件持久化",
  "operations": [
    {
      "name": "load",
      "summary": "读取 todos 文件并解析为列表",
      "inputs": [
        { "name": "path", "type": "string", "required": false, "description": "文件路径，默认 ./todos.json" }
      ],
      "outputs": [
        { "name": "todos", "type": "Todo[]", "required": true, "description": "待办列表" }
      ],
      "errors": ["ERR-STORE-001"]
    }
  ]
}
```

**`InterfaceSpec`：** `{ "name", "module_ref", "file", "protocol", "description"?, "operations": OperationSpec[] }`

**`OperationSpec`：** `{ "name", "summary", "description"?, "inputs": ParamSpec[], "outputs": ParamSpec[], "errors"?: string[], "http"?, "idempotent"?, "notes"? }`

**`ParamSpec`：** `{ "name", "type", "required": boolean, "description", "default"?, "schema_ref"? }` — `schema_ref` 指向 `data_model[].name` 或 §4.5 类型。

**`protocol` 枚举：** `internal` | `cli` | `http` | `grpc` | `websocket`

**校验：** `DES-032`–`034`；类图 `classDiagram`（P1）。

与 §4.2 分工：§4.2 写 **模块边界与职责**；§4.4 写 **可调用契约**（签名级）。

### §4.5 Data Model & Table Schema（表结构 / 数据结构设计）

回答：**逻辑实体 + 物理表/集合/文件结构**（有 DB 须到字段级；无 DB 须到 JSON/文件字段级）。

**逻辑模型** — `data_model[]`：实体、关系、不变量。

#### 字段规范（每条 column **必填**）

| 要求 | 说明 | JSON |
|------|------|------|
| **可空明确** | 每字段 **必须** 写 `nullable: true/false`，禁止省略 | `ColumnDef.nullable` |
| **注释** | 每字段 **必须** 有业务含义说明 | `ColumnDef.description` |
| 类型 | SQL/JSON/链上类型写全 | `ColumnDef.type` |
| 键 | PK / UK 标注 | `pk`, `unique` |

推荐表格列：**字段 | 类型 | 可空（是/否）| 键 | 注释**

#### 审计字段（表级）

**关系型 / 文档库表**（`storage` 为 `postgresql`、`mysql`、`mongodb` 等）**须** 包含：

| 字段 | 类型（推荐） | 可空 | 说明 |
|------|--------------|------|------|
| `created_at` | `timestamptz` / `datetime` | 否 | 创建时间 |
| `updated_at` | `timestamptz` / `datetime` | 否 | 最后更新时间 |
| `version` | `integer` / `bigint` | 否 | **推荐** — 乐观锁 / 并发控制；不需要时在 `audit_policy` 说明 |

JSON：`table_schemas[].audit_policy` → `{ "require_created_at": true, "require_updated_at": true, "require_version"?: boolean, "notes"?: string }`

**文件 / JSON 单文件**（如 `todos.json`）：若无表级时间戳，须在 `audit_policy.notes` 说明（如「实体级不设时间戳；依赖文件 mtime」或「JSON 元素含 `created_at`」）。

#### 索引设计

**须** 为每张表设计 **合理索引**（非仅 PK）：

| 要求 | 说明 |
|------|------|
| 查询驱动 | 每个常用 WHERE / ORDER BY / JOIN 列有索引或说明为何不需要 |
| 登记 | `indexes[]` 结构化对象；**关系型 DB** 须有条目或 `notes` 说明仅 PK/全表扫描可接受；**文件/JSON 单文件** 允许 `indexes: []` + `notes` |
| 唯一约束 | 业务唯一键用 `unique: true` 索引或列级 `unique` |

JSON **`IndexDef`**：`{ "name", "columns": string[], "unique"?: boolean, "type"?: "btree"|"hash"|"gin"|..., "purpose" }` — `purpose` 为注释（为何建此索引）。

**TableSchema 完整示例：**

```json
{
  "name": "todos",
  "storage": "postgresql",
  "audit_policy": {
    "require_created_at": true,
    "require_updated_at": true,
    "require_version": true
  },
  "columns": [
    { "name": "id", "type": "uuid", "nullable": false, "pk": true, "description": "主键" },
    { "name": "text", "type": "varchar(500)", "nullable": false, "description": "待办正文" },
    { "name": "done", "type": "boolean", "nullable": false, "description": "是否完成，默认 false" },
    { "name": "created_at", "type": "timestamptz", "nullable": false, "description": "创建时间 UTC" },
    { "name": "updated_at", "type": "timestamptz", "nullable": false, "description": "最后更新时间 UTC" },
    { "name": "version", "type": "integer", "nullable": false, "description": "乐观锁版本号，从 1 起" }
  ],
  "indexes": [
    { "name": "idx_todos_done_updated", "columns": ["done", "updated_at"], "type": "btree", "purpose": "list 按完成状态筛选并排序" }
  ]
}
```

无关系库时：`storage: "todos.json"`，仍须 **可空 + 注释**；审计字段按实体或 `audit_policy.notes` 说明。

**校验：** `DES-013`、`DES-018`–`020`。

### §4.6 Flow（时序图 / 流程图 — 必填）

回答：**主路径怎么跑**；**须** 在 `*.mmd` 中提供图，并在正文引用。

| 要求 | 说明 |
|------|------|
| **至少 1 张时序图** | `sequenceDiagram` — 主业务/命令/请求链（`DES-203`、`DES-214`） |
| **至少 1 张流程图** | `flowchart` — 分支、重试、异常路径（`DES-214`）；可与时序同文件或 `flow.mmd` 多段 |
| 登记 | `diagrams[]` 含 `kind: sequence` **与** `kind: flowchart` |
| 命名 | participant / 节点与 `modules[]`、`interfaces[]` 一致（`DES-204`） |

正文须写清：**正常路径** + **关键异常分支**（与 §6 错误码对应）。

### §6 Cross-cutting Concerns

除 Security / Configuration / Observability 外，**固定两子节**：

#### §6.1 Data Consistency & Transactions（数据一致性 / 事务约束）

承接 spec `consistency_profile`，写 **实现层约束**：

| 项 | 说明 |
|----|------|
| 事务边界 | 哪些操作在同一事务 / 同一原子单元 |
| 隔离级别 | DB `READ COMMITTED` / 链上 nonce 等 |
| 幂等 | 幂等键、去重窗口 |
| 跨服务 | Saga / 最终一致 / 补偿 |
| 失败恢复 | 回滚、重试、对账 |

JSON：`transaction_constraints[]` → `{ "id", "scope", "boundary", "isolation"?, "idempotency"?, "consistency_ref"?, "notes"? }` — `id` 推荐 `TX-{域}-{序号}`（如 `TX-STORE-001`）

无 DB 时仍须写 **文件/单进程** 原子写、锁、重入约束（如 CLI Todo 的 temp+rename）。

#### §6.2 Errors & Error Codes（异常 / 错误码）

**须** 定义可实现的错误目录；**`code` 须符合 [编码规范](#编码规范错误码--测试用例)**。

| 码 | 名称 | 场景 | 用户/调用方可见 | 可重试 | 恢复/处理 |
|----|------|------|-----------------|--------|-----------|

JSON：`error_catalog[]` → `{ "code", "name"?, "http_status"?, "message", "when", "retryable"?, "recovery" }`

Flow 流程图节点建议标注 `ERR-*` 码（如 `ERR-STORE-001`），与下表一致。

其它横切：`cross_cutting.security`、`cross_cutting.configuration`、`cross_cutting.observability`（或 §10）。

### §5 Alternatives Considered

- 表格：Option | Decision（选用/拒绝）| 理由。
- JSON：`decisions[]` → `{ "id": "ADR-1", "option", "decision": "accepted"|"rejected", "rationale" }` — **`id` 用 `ADR-{序号}`**（与 `ALT-*` 同义，统一 ADR）。

### §7 Performance & Reliability

承接 spec §8 **定性档位**，在本节写 **可测数值**（延迟、吞吐、可用性、RPO/RTO…）。

| spec 字段 | design 落点 |
|-----------|-------------|
| `operational_profile` | `non_functional[]` 指标 + `target` + `verification` |
| `consistency_profile` | §6.1 `transaction_constraints[]` + 可选 NFR |

JSON：`non_functional[]` → `{ "id": "NFR-1", "source"?, "metric", "target", "verification" }`

### §8 Testing Plan + 附录 D 测试用例设计

**§8** — 策略：层次（单测/集成/E2E/fork）、工具、通过标准、**覆盖率目标**（P0 功能 + **全部错误码**）。

**附录 D** — **测试用例设计**（须 **正向 + 异常 + 边界** 全覆盖）；**`id` 须符合 [编码规范](#编码规范错误码--测试用例)**。

| ID | 类型 | 标题 | 前置条件 | 步骤 | 期望结果 | 覆盖 AC/US | 错误码 |
|----|------|------|----------|------|----------|------------|--------|

**`kind`（类型）枚举 — 必填：**

| kind | 含义 | ID 中段 | 要求 |
|------|------|---------|------|
| `happy` | 正向 / 主路径 | `HAP` | 每个 P0 **FEAT** 或 **US** 至少 1 条 |
| `negative` | 异常 / 失败 | `NEG` | **每个** `error_catalog[].code` 至少 1 条 |
| `boundary` | 边界 | `BND` | 空输入、超长、并发等（按 spec 适用） |

**覆盖规则：**

1. 每个 P0 **AC** 至少 1 条用例（`covers` 含 AC id）— `DES-016`  
2. **每个错误码** 至少 1 条 `kind=negative` 用例，`error_code` **等于** §6.2 的 `code` — `DES-021`  
3. 主路径 + 异常路径与 §4.6 flowchart 分支一致  
4. §8 声明覆盖矩阵：`FEAT/US/AC` × `happy/negative/boundary`（可表格）

JSON **`TestCase`**：

```json
{
  "id": "TC-NEG-STORE-001",
  "kind": "negative",
  "title": "损坏 JSON 拒绝加载",
  "preconditions": "todos.json 非法 JSON",
  "steps": ["todo list"],
  "expected": "exit 1，stderr 含 ERR-STORE-001",
  "covers": ["AC-1"],
  "error_code": "ERR-STORE-001"
}
```

路径清单：`test_strategy.paths[]`（测试代码内 assert 建议使用同一 `ERR-*` / `TC-*` 常量）。

---

## 编码规范（错误码 & 测试用例）

**原则：** 一眼看出 **类型 + 所属模块或外部服务**；**不同模块、不同外部服务 → 不同 `{域}` 前缀**，禁止混用。

### 域前缀注册（模块 & 外部服务）

设计阶段须在 **§4.2 / §4.3** 声明 **`code_domain` 注册表**（JSON 同步写入 `modules[]`、`external_dependencies[]`）：

| 所有者类型 | 来源 | code_domain 规则 | 示例 |
|------------|------|------------------|------|
| **模块** | `modules[]` | 每个模块 **唯一** 域 | `TodoCLI`→`CLI`，`TodoStore`→`STORE`，`SpreadEngine`→`ENG` |
| **外部服务** | `external_dependencies[]`（`db`/`cache`/`rpc`/`api`/`blockchain`） | 每个依赖 **唯一** 域，**不得**与模块或其它服务重复 | `Redis`→`REDIS`，`Uniswap RPC`→`UNIV3`，`PostgreSQL`→`PG` |
| **本地文件** | `kind=filesystem` | 可 **复用封装模块** 域；`failure_behavior` 或 `notes` 说明 | `todos.json`→`STORE` |
| **无中间件** | `kind=none` | **不分配** `code_domain` | 占位行「无外部依赖」 |

**Connector 与 RPC：** DEX Connector 为 **`modules[]` 模块**（如 `UniswapConnector`，`code_domain=UNIV3`）；链上 RPC 节点为 **`external_dependencies[]`**（`kind=rpc`）。若 RPC 错误由 Connector **统一封装**，只登记模块域，**不**再单独为 RPC 建域；若需区分直连 RPC 故障，可为 RPC 单独设域（如 `UNIV3RPC`），且不得与模块域重复。

**归属规则（谁出错用谁的域）：**

```text
模块内逻辑错误     → ERR-{模块.code_domain}-*
调用 Redis 失败    → ERR-{redis.code_domain}-*   （不是 ERR-STORE-*）
CLI 参数校验失败   → ERR-{CLI.code_domain}-*
跨模块集成测试     → TC-*-{被断言模块.code_domain}-*
```

**套利示例（多服务）：**

| 所有者 | 登记位置 | code_domain | 错误码示例 |
|--------|----------|-------------|------------|
| SpreadEngine | `modules[]` | `ENG` | `ERR-ENG-001` |
| UniswapConnector | `modules[]` | `UNIV3` | `ERR-UNIV3-001` |
| CamelotConnector | `modules[]` | `CAMELOT` | `ERR-CAMELOT-001` |
| Redis | `external_dependencies[]` | `REDIS` | `ERR-REDIS-001` |
| PostgreSQL | `external_dependencies[]` | `PG` | `ERR-PG-001` |

校验：`DES-027`–`031`（域唯一、错误码/用例域已注册）。

### 错误码 `code`

| 项 | 规则 |
|----|------|
| **格式** | `ERR-{域}-{序号}` |
| **域 `{域}`** | **必须** 来自已注册的 `modules[].code_domain` 或 `external_dependencies[].code_domain` |
| **序号** | **3 位**数字，`001` 起，**按域内**递增（各域独立计数） |
| **禁止** | 跨模块共用同一 `{域}`；`E001` 等无域短码 |

**示例：**

| code | 域 | 含义 |
|------|-----|------|
| `ERR-STORE-001` | TodoStore | JSON 解析失败 |
| `ERR-STORE-002` | TodoStore | 磁盘不可写 |
| `ERR-CLI-001` | TodoCLI | 参数非法 |

HTTP 服务可在 JSON 另填 `http_status`；响应 body 业务码仍用 `ERR-{服务.code_domain}-*`。

**`SYS` 域（可选）：** 进程级无法归属故障。须在 `modules[]` **显式注册** `{ "name": "System", "path": "—", "responsibility": "进程级", "code_domain": "SYS" }`（无对应 `interfaces` 条目，`DES-032` 豁免）；`error_catalog` 备注原因；**不宜超过 3 条**。

### 测试用例 `id`

| 项 | 规则 |
|----|------|
| **格式** | `TC-{种类}-{域}-{序号}` |
| **种类** | `HAP` \| `NEG` \| `BND` ↔ `kind` |
| **域 `{域}`** | **必须** 为已注册域；表示 **被测模块** 或 **被测外部服务**（测 Redis 超时 → `REDIS`，不是 `ENG`） |
| **序号** | 3 位，**按 `种类+域`** 独立递增 |
| **禁止** | 多模块共用一个 `{域}`；`TC-1` 作正式 id |

**示例：**

| id | kind | 说明 |
|----|------|------|
| `TC-HAP-CLI-001` | happy | add + list 主路径 |
| `TC-HAP-STORE-001` | happy | 重启后仍可读 |
| `TC-NEG-STORE-001` | negative | 对应 `ERR-STORE-001` |
| `TC-NEG-STORE-002` | negative | 对应 `ERR-STORE-002` |
| `TC-BND-CLI-001` | boundary | 超长标题（501 字符） | 截断或拒绝 |
| `TC-NEG-REDIS-001` | negative | Redis 超时；对应 `ERR-REDIS-001`（域=服务） |

**联动：**
- `kind=negative` 时 **必须** 填 `error_code`；`{域}` 宜与 `id` 一致（`DES-031`）。
- `kind=boundary` 时 **默认不填** `error_code`；若边界行为触发 catalog 中已有码，可填且须与 `id` 域一致。

### 其它设计 id（可选对齐）

| 类型 | 格式 | 示例 |
|------|------|------|
| 事务约束 | `TX-{域}-{序号}` | `TX-STORE-001` |
| NFR | 已有 `NFR-{序号}` | `NFR-1` |
| ADR | `decisions[].id` 用 **`ADR-{序号}`** | `ADR-1` |

---

## 七项必备 — 速查

| # | 内容 | 位置 | JSON |
|---|------|------|------|
| 1 | 外部依赖 DB/Redis/服务 | §4.3 | `external_dependencies[]` |
| 2 | **模块 API（入参/出参/行为）** | §4.4 | `interfaces[]` → `operations[]` |
| 3 | 表结构（可空+注释+索引+审计字段） | §4.5 | `table_schemas[]` |
| 4 | 时序图 + 流程图 | §4.6 + `*.mmd` | `diagrams[]` |
| 5 | 测试用例（happy/negative/boundary） | 附录 D | `test_cases[]` |
| 6 | 数据一致性 / 事务 | §6.1 | `transaction_constraints[]` |
| 7 | 异常 / 错误码 | §6.2 | `error_catalog[]` |

---

## 示例说明

Todo 为 Profile=`default` **教学 fixture**（非套利业务）；与 [`spec.md`](./spec.md)、[`schemas/design.md`](../schemas/design.md) 示例对照。套利业务见 [`arb-core-design.md`](../../../arb-core-design.md)。下文为 **章节齐全的整篇样例**（§1–§11 + 附录 A–E）。

---

## 样例文档 — default Profile（CLI Todo）

> 对应 spec 示例「CLI Todo App」；Run 路径：`docs/factory/runs/<task_id>/design.md`

```markdown
# Design Doc — CLI Todo App

- **Revision：** 1
- **Spec：** CLI Todo App
- **Status：** draft

## 1. Context & Background

实现 spec r1：命令行 Todo 增删查与 JSON 持久化（FEAT-1、FEAT-2）。单用户本地工具，无网络。

| 名称 | 类型 | 说明 |
|------|------|------|
| 用户 | 人 | 终端操作 |
| todos.json | 外部文件 | 持久化 |

## 2. Goals

- CRUD 稳定；持久化可单测（KPI-2）
- **Constraints：** `no_secrets_in_repo`；spec 性能 `best_effort`、一致性 `local_only`

## 3. Non-Goals

- Web UI、多用户（spec scope_out）
- 云同步、Redis、PostgreSQL

## 4. Design

### 4.1 Overview

CLI 解析子命令 → TodoStore 读写 JSON 文件。

### 4.2 Components

| 模块 | 路径 | 职责 | code_domain |
|------|------|------|-------------|
| TodoCLI | src/cli.py | 子命令 | CLI |
| TodoStore | src/todo_store.py | JSON 读写 | STORE |

### 4.3 External Dependencies

| 名称 | 类型 | 技术 | 用途 | code_domain | 关键性 |
|------|------|------|------|-------------|--------|
| todos.json | filesystem | 本地文件 | 持久化 | STORE | required |

无 Redis / DB / 外部 HTTP。

### 4.4 APIs

#### TodoCLI（`src/cli.py` · `cli` · `CLI`）

| 操作 | 功能说明 | 入参 | 出参 | 错误码 |
|------|----------|------|------|--------|
| `add` | 添加待办 | `text`: string，必填，正文 | exit 0；stdout 可选确认 | `ERR-CLI-001`（空标题） |
| `list` | 列出全部待办 | — | stdout: `Todo[]` 格式化输出 | 透传 `ERR-STORE-001` |
| `done` | 标记完成 | `id`: string(uuid)，必填 | exit 0 | `ERR-CLI-001`（非法 id）；透传 Store 错误 |

#### TodoStore（`src/todo_store.py` · `internal` · `STORE`）

| 操作 | 功能说明 | 入参 | 出参 | 错误码 |
|------|----------|------|------|--------|
| `load` | 读取并解析 JSON 文件 | `path`: string，可选，默认 `./todos.json` | `Todo[]` | `ERR-STORE-001` |
| `save` | 原子写入全量列表 | `todos`: `Todo[]`，必填；`path`?: string | `void` | `ERR-STORE-002` |
| `append` | 追加一条并持久化 | `todo`: `Todo`（无 id 时内部生成） | `Todo`（含 id、时间戳） | `ERR-STORE-002` |

### 4.5 Data Model & Table Schema

**逻辑：** Todo { id, text, done, created_at, updated_at }

| 字段 | 类型 | 可空 | 键 | 注释 |
|------|------|------|-----|------|
| id | string (uuid) | 否 | PK | 唯一标识 |
| text | string | 否 | — | 待办正文 |
| done | boolean | 否 | — | 是否完成 |
| created_at | string (ISO8601) | 否 | — | 创建时间 |
| updated_at | string (ISO8601) | 否 | — | 最后修改时间 |

**audit_policy：** 实体级时间戳；**indexes：** 无（personal 规模全量 load，见 notes）

### 4.6 Flow

- **时序图：** [flow.mmd](./flow.mmd) — `add`（sequenceDiagram）
- **流程图：** [flow.mmd](./flow.mmd) — 持久化与 ERR-STORE-* 分支（flowchart）

## 5. Alternatives Considered

| Option | Decision | 理由 |
|--------|----------|------|
| JSON 文件 | accepted | spec json_file；零依赖 |
| SQLite | rejected | 超出 scope |

（JSON：`decisions[]` → `{ "id": "ADR-1", "option": "JSON 文件", "decision": "accepted", "rationale": "…" }`）

## 6. Cross-cutting Concerns

### 6.1 Data Consistency & Transactions

| ID | 范围 | 边界 |
|----|------|------|
| TX-STORE-001 | save | temp + rename；spec local_only |

### 6.2 Errors & Error Codes

| 码 | 场景 | 可重试 | 处理 |
|----|------|--------|------|
| ERR-CLI-001 | CLI 参数非法（如空标题） | 否 | exit 2 |
| ERR-STORE-001 | JSON 解析失败 | 否 | exit 1 |
| ERR-STORE-002 | 磁盘不可写 | 是 | 提示权限 |

## 7. Performance & Reliability

| ID | 指标 | 目标 |
|----|------|------|
| NFR-1 | 交互 | 单命令 < 500ms（manual） |

## 8. Testing Plan

pytest 单测；覆盖全部 AC 与 error_catalog；矩阵见附录 D。

## 9. Rollout & Deployment

N/A — 本地单进程 CLI。

## 10. Monitoring & Alerting

N/A — 无长期服务。

## 11. Open Questions

None

## 附录 A. 需求追溯

| spec id | 设计落点 |
|---------|----------|
| FEAT-1 | TodoCLI, T2 |
| FEAT-2 | TodoStore, T1 |
| AC-1 | tests/test_todo.py, TC-HAP-CLI-001–TC-NEG-STORE-002, TC-NEG-CLI-001, TC-BND-CLI-001 |

## 附录 B. 文件变更计划

| 路径 | 操作 | 原因 |
|------|------|------|
| src/todo_store.py | create | 持久化 |
| src/cli.py | create | CLI |
| tests/test_todo.py | create | AC-1 |

## 附录 C. 开发任务分解

| ID | 路径 | 描述 | 依赖 |
|----|------|------|------|
| T1 | src/todo_store.py | load/save/append | — |
| T2 | src/cli.py | 子命令 | T1 |

## 附录 D. 测试用例设计

| ID | 类型 | 标题 | 期望 | 覆盖 | 错误码 |
|----|------|------|------|------|--------|
| TC-HAP-CLI-001 | happy | 添加待办 | 列表含项 | AC-1, US-1 | — |
| TC-HAP-STORE-001 | happy | 重启持久化 | 数据仍在 | US-2 | — |
| TC-NEG-CLI-001 | negative | 空标题 | 拒绝 | US-1 | ERR-CLI-001 |
| TC-NEG-STORE-001 | negative | 损坏 JSON | exit 1 | AC-1 | ERR-STORE-001 |
| TC-NEG-STORE-002 | negative | 磁盘不可写 | ERR-STORE-002 提示 | — | ERR-STORE-002 |
| TC-BND-CLI-001 | boundary | 超长标题 | 截断或拒绝 | US-1 | — |

实现路径：`tests/test_todo.py`

## 附录 E. 与现有代码对照

`code_root` 空仓库；本次全部为 create。
```

**套利 / 服务类任务：** 章节结构 **相同**；§4.3 改为 RPC/Redis/DB，§4.5 为真实表与索引，§9–§10 非 N/A。参考 [`arb-core-design.md`](../../../arb-core-design.md)。

---

## 实现提示

- HITL 必读：**§4.3–§4.6（含 §4.4 API 入参/出参）、§6.1–§6.2、flow.mmd、附录 D**。
- 渲染器：`multi_agent_code_factory/renderers/design_md.py`（P1）。
- 真源：`design.json`。
