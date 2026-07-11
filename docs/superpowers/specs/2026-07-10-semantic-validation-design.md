# Semantic Validation — 设计说明

> **日期：** 2026-07-10  
> **状态：** 草案 v4（评审修订 · 与 [PRD 全栈命名](./2026-07-10-prd-artifact-rename-design.md) 对齐）  
> **关联规范：** [`quality-gates/prd-validate.md`](../../design/pipeline/quality-gates/prd-validate.md)（R4 由 `spec-validate.md` 重命名） · [`quality-gates/design-validate.md`](../../design/pipeline/quality-gates/design-validate.md) · [`artifact-schemas/prd-spec.md`](../../design/pipeline/artifact-schemas/prd-spec.md) · [`PRD 全栈命名`](./2026-07-10-prd-artifact-rename-design.md)

## 修订记录

| 版本 | 变更 |
|------|------|
| v1 | 初稿 |
| v2 | 修正 TC id 与 DES-024 冲突；统一 dimensions 语法；收窄触发条件；SPEC-S05 去掉不存在的 `covers`；DES-S01 按 `kind` 分支 + DES-S01b 枚举覆盖；回归表拆分 spec/design；补充 `prompt_context_trim` |
| v3 | Run 产物统一为 `prd.json` / `prd.md` |
| v4 | rule_id **`SPEC-*` → `PRD-*`**、**`SPEC-S*` → `PRD-S*`**；`PrdArtifact`；节点 `prd_validate`（见 PRD 全栈命名设计） |
| v4.1 | **双层 enforcement**：blocking / advisory 分级 + `semantic_block_on`；**语义 warn 主动注入下游 prompt**；`trim_design(compact)` 保留 `test_cases` |

## 背景

`calculator-10-01` 暴露了一类流水线失效：**格式校验通过，语义校验缺失**。

- `prd_validate` / `design_validate` 现有 **49 + 57** 条规则主要检查：字段非空、id 唯一、章节齐全、`covers` 含 AC id、错误码配对等。
- 未检查：**US 意图 ↔ REQ ↔ test_cases ↔ error_catalog** 是否在同一语义模型下自洽。
- 结果：实现按 AC 示例的**句法投影**（如 `split()` 成 3 段）过关，但不符合 US 语义（「两数一符」应接受 `1*2`）；混合运算边界仅写在 `scope_out`，未落成可测语义。

**根因归类：**

| 现象 | 类型 | 现有门禁 |
|------|------|----------|
| `1*2` 不支持 | 语义等价类未覆盖（非空格问题） | 无 |
| `1+2+3` 是否支持 | 语义排除未结构化 | 无 |
| prd.md 章节齐全 | 格式 | PRD-301～316 ✓ |

本设计在 quality-gates 中新增 **语义校验层（PRD-S\* / DES-S\*）**，与既有格式规则并列，不替代。

## 目标

1. 机器可判定：用户输入/行为的**语义约束**（元数、类型、排除项），不绑定具体分隔符或示例字面量。
2. PRD（`prd.json`）为语义契约**唯一来源**；Design 产出可审计的**语义证据**（test_cases）。
3. 通用：适用于自由格式输入、API 请求体、表单等任务；**不**因 `interface=cli`  alone 强迫子命令型 CLI 套用 `input_shape`。
4. 语义规则分 **blocking（硬门禁）** 与 **advisory（启发式）**；P2 起 blocking 默认 **error**，advisory 默认 **warn**；未达标时 **warn 亦注入下游 Agent prompt**（见 §双层 enforcement）。

## 非目标

- 不用 prompt-only 替代语义门禁（已否决方案 A）。
- V1 不做全自然语言语义理解（不用 LLM 作为唯一校验器）。
- V1 不校验生成代码的静态语义（P5 靠 Developer 原则，非 DES-S 硬门禁）；先卡住 Spec / Design 环。
- 不修改既有 `calculator-10-01` run 产物（仅作回归样例）。

## 决策摘要

| 项 | 决策 |
|----|------|
| 语义契约存放 | **PRD 层**（`prd.json`）`semantic_constraints[]`；Design 只引用 + 产出 evidence |
| 规则严格度 | **双层**：blocking 规则 P2 起默认 **error**；advisory 默认 **warn** 至 P4；Profile `validation.*.semantic_block_on` 可整体降级为 warn（legacy 兼容） |
| 软 enforcement | **`passed=true` 且存在 PRD-S\*/DES-S\* warn 时**，仍写入 `semantic_advisories_*` 注入 Architect / Developer / Reviewer prompt（P2 必做） |
| 与格式规则关系 | 独立 rule_id 段 **PRD-S\*** / **DES-S\***；PRD 环结构规则为 **PRD-001～PRD-316**（由原 SPEC-* 整体改号） |
| 触发策略 | **窄触发**强制 SEM；`interface=cli`  alone 不强制（见 §触发条件） |
| `SEM-*` 追溯 | 不进 `traceability`（仅 FEAT/AC）；通过 `test_cases.covers` + `semantic_evidence.constraint_ref` 追溯 |
| LLM 辅助 | 可选 P6 `semantic_review` 节点，过渡 lint，不阻塞 V1 |

---

## 架构

### 三层校验

```text
┌──────────────────────────────────────────────────────────────┐
│  Layer 1 — Structure   PRD-001～017, DES-001～036           │
│  字段存在、id 唯一、依赖无环                                    │
├──────────────────────────────────────────────────────────────┤
│  Layer 2 — Format      PRD-301～316, DES-201～224           │
│  prd.md / design.md 章节、表格、元数据                         │
├──────────────────────────────────────────────────────────────┤
│  Layer 3 — Semantic    PRD-S01～S06, DES-S01～S01b, DES-S02～S05 │
│  意图一致、语义维度覆盖、排除项可测、枚举值覆盖                  │
└──────────────────────────────────────────────────────────────┘
```

### 语义对象模型（通用）

```text
Intent (US/FEAT)
    → Constraint (semantic_constraints.dimensions)
    → Exclusion (semantic_constraints.excludes / scope_out)
    → Evidence (design.test_cases.semantic_evidence)
```

| 概念 | 含义 | 校验什么 |
|------|------|----------|
| **Intent** | 用户可观察目标 | FEAT 不得宽于 US |
| **Constraint** | 必须成立的语义条件 | 每个 dimension 有 evidence（按 `kind` 分支） |
| **Exclusion** | 必须拒绝的语义越界 | 有 negative TC |
| **Evidence** | 可执行证明 | 见 §DES-S01 / DES-S01b（按 `kind` 不同） |

**语义维度示例**（统一规则语法，见下节）：

- `operand_count: exactly:2`
- `operator_count: exactly:1`
- `operator_set: one_of:+, -, *, /`
- `operand_type: type:number`

空格、逗号等**表面格式**不在 `dimensions` 中约束；由 `input_shape` 的**等价类证据**（DES-S01）间接保证未过度锚定单一示例。

### `kind` 与适用场景

| `kind` | 适用 | 典型任务 |
|--------|------|----------|
| `input_shape` | 自由格式、需解析的输入 | 计算器表达式、搜索框、JSON body |
| `command_shape` | 子命令 + 参数（V2 细化 dimensions） | Todo `add/list/done` |
| `output_shape` | 输出结构约束 | API 响应 schema |
| `state_transition` | 多步状态变化 | 订单状态机 |
| `invariant` | 始终成立的规则 | 除零必拒、幂等 |

V1 门禁与示例以 **`input_shape`** 为主；`command_shape` 的 dimensions 模板留 V2（见开放问题）。

---

## PRD 契约：`semantic_constraints[]`

> Run 落盘：`prd.json`（机器读）、`prd.md`（人读）。Pydantic 类型为 **`PrdArtifact`**（`schemas/prd.py`）；校验节点为 **`prd_validate`**。

### 新增字段（`prd.json` 顶层）

```json
"semantic_constraints": [
  {
    "id": "SEM-IN-1",
    "source_ref": "US-1",
    "source_kind": "US",
    "kind": "input_shape",
    "summary": "单次二元算术输入",
    "dimensions": {
      "operand_count": "exactly:2",
      "operator_count": "exactly:1",
      "operator_set": "one_of:+, -, *, /",
      "operand_type": "type:number"
    },
    "excludes": [
      {
        "id": "EX-CHAIN",
        "dimension": "operand_count",
        "rule": "gte:3",
        "summary": "链式或混合运算（三个及以上操作数）"
      }
    ],
    "notes": "表面分隔符不在 dimensions；由 design 等价类证据覆盖"
  }
]
```

### 类型定义（`schemas/prd.py`）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | `SEM-{DOMAIN}-{###}`（三位数字，与 TC id 规则一致） |
| `source_ref` | string | 是 | 关联 `US-*` / `FEAT-*` / `REQ-*` |
| `source_kind` | enum | 是 | `US` \| `FEAT` \| `REQ` |
| `kind` | enum | 是 | `input_shape` \| `command_shape` \| `output_shape` \| `state_transition` \| `invariant` |
| `summary` | string | 是 | 人读一句 |
| `dimensions` | object | 是 | 键为维度名；**值必须为规则语法字符串**（见下） |
| `excludes` | array | 否 | 语义越界条目 |
| `excludes[].id` | string | 是 | `EX-*` |
| `excludes[].dimension` | string | 是 | 指向 `dimensions` 键或扩展维度 |
| `excludes[].rule` | string | 是 | 规则语法字符串 |
| `excludes[].summary` | string | 是 | 人读 |
| `notes` | string | 否 | |

### 规则语法（V1 白名单，唯一合法写法）

所有 `dimensions` 与 `excludes[].rule` 的值**必须**匹配下列前缀之一：

| 前缀 | 示例 | 含义 |
|------|------|------|
| `exactly:N` | `exactly:2` | 计数恰好 N |
| `gte:N` / `lte:N` | `gte:3` | 计数边界 |
| `one_of:a,b,c` | `one_of:+, -, *, /` | 枚举集合（逗号分隔，允许符号周围空格） |
| `type:number` | `type:number` | 操作数/字段类型 |
| `type:string` | `type:string` | |
| `type:boolean` | `type:boolean` | |

**禁止**裸写 `number`、`+, -, *, /` 等非前缀形式（校验器 PRD-S02b 可选校验语法合法性，V1 warn）。

### 触发条件（何时 `semantic_constraints` 须非空）

采用 **窄触发**；满足 **任一** 即要求 `semantic_constraints` 非空：

1. **自由格式输入信号**（组合启发式，中/英）  
   - `user_stories[].want` 或 `features[].description` 含：`输入`/`解析`/`parse`/`expression`/`submit`/`upload` 等 **且** 含可解析对象（数字、表达式、请求、文件）  
   - **或** `context.glossary` 含 term 匹配 `/表达式|请求体|输入格式|input/i`

2. **`context.interface` ∈ `api` · `web` · `form`**（默认存在结构化输入契约）

**不触发**（`semantic_constraints` 可为 `[]`）：

- 仅 `interface=cli` 且为**子命令型**（如 `add/list/done`，无自由表达式解析）的 Todo 类任务
- 无用户输入的批处理 / 纯库任务

> **说明：** 计算器同时满足 (1) 与 `interface=cli`，会触发。Todo CLI 仅 `interface=cli` **不**触发，避免强行编造 `operand_count`。

**PRD-S01** 在窄触发成立且 `semantic_constraints` 为空时 warn。

### 人读映射（`prd.md`）

在 `## 需求池` 之后新增 **`## 语义约束`**（窄触发时必填）：

```markdown
## 语义约束

| ID | 来源 | 类型 | 摘要 |
|----|------|------|------|
| SEM-IN-1 | US-1 | input_shape | 单次二元算术输入 |

**维度：** operand_count=exactly:2；operator_count=exactly:1；operator_set=one_of:+, -, *, /；operand_type=type:number

**明确排除：** 链式/混合运算（operand_count≥3）
```

渲染器：`renderers/prd_md.py`（输出 `prd.md`）；格式规则：**PRD-S06**（warn）。

---

## Design 证据：`test_cases[].semantic_evidence`

### 扩展 `TestCase`（`schemas/design.py`）

`test_cases[].id` **必须**符合既有 **DES-024**：`TC-{HAP|NEG|BND}-{DOMAIN}-\d{3}`（三位数字，**无**字母后缀）。等价类用 `semantic_evidence.equivalence_class` 区分，不改 id。

**示例（同一 SEM 下两条 happy TC）：**

```json
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
}
```

```json
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
```

四则运算符枚举覆盖另需 TC（可与上例组合满足 DES-S01b），例如 `TC-HAP-CALC-010`（`input: "10 / 2"`）、`TC-HAP-CALC-011`（`input: "10 - 2"`）。

| 字段 | 说明 |
|------|------|
| `semantic_evidence.constraint_ref` | 引用 `prd.json` 中 `semantic_constraints[].id` |
| `semantic_evidence.equivalence_class` | 同一语义下的句法变体标识（Architect 命名，非 TC id） |
| `semantic_evidence.proves_dimensions` | 本 TC 证明哪些 dimension **键** |
| `description` | 须含可解析字面量：`input: "..."` 或 `request: {...}` |

### 证据规则按 `kind` 分支（DES-S01 / DES-S01b）

| constraint `kind` | 规则 | 判定 |
|-------------------|------|------|
| `input_shape` | **DES-S01** | 每个 `SEM-*`：≥2 happy TC 的 `equivalence_class` 不同；`proves_dimensions` 并集 = 该 constraint 的 `dimensions` 键集 |
| `input_shape` + `one_of:` 维度 | **DES-S01b** | 对每个 `one_of:a,b,c` 维度，`description` 中 `input:`/`request:` 须覆盖 **每个枚举值至少一次**（如四个运算符各至少一条 happy TC） |
| `invariant` | **DES-S01**（invariant 分支） | 每个 `SEM-*`：≥1 happy 或 boundary TC + ≥1 negative TC 引用该 constraint；**不要求**等价类 |
| `state_transition` | **DES-S01**（transition 分支） | 每个 `SEM-*`：≥1 TC 且 `steps` 非空；**不要求**等价类 |
| `output_shape` | **DES-S01**（output 分支） | 每个 `SEM-*`：≥1 TC 在 `expected` 或 `description` 体现输出约束；V1 warn |

### `error_catalog` 语义化（DES-S02）

`when` / `message` 须描述**语义违反**，禁止仅引用单一示例字面量：

| 差 | 好 |
|----|-----|
| 不符合「操作数 运算符 操作数」格式 | 操作数不是恰好 2 个，或运算符不是恰好 1 个 |
| 请使用 3 + 5 | 请输入两个数字和一个运算符（如 3+5 或 3 + 5） |

---

## 语义校验规则

### PRD 环 — `PRD-S01`～`PRD-S06`

（由 `prd_validate` 节点执行；报告写入 `prd_validation.json`。）

| rule_id | 分级 | 严重度 P2 默认 | 触发 | 判定 |
|---------|------|----------------|------|------|
| **PRD-S01** | blocking | error | §窄触发条件 | `semantic_constraints` 非空 |
| **PRD-S02** | blocking | error | 有 `semantic_constraints` | 每条 `source_ref` 引用存在的 US/FEAT/REQ |
| **PRD-S02b** | advisory | warn | 有 `semantic_constraints` | 每条 `dimensions` / `excludes[].rule` 符合规则语法白名单 |
| **PRD-S03** | advisory | warn | `scope_out` 非空 | 每条 scope_out 在**任一** `semantic_constraints[].excludes` 或**任一** `requirement_pool[].description` 有可匹配关键词（中英启发式：链式/混合/GUI/持久化/chained/mixed 等） |
| **PRD-S04** | advisory | warn | P0 FEAT 有 `user_story_ids` | FEAT.description 不得宽于 US.want（启发式：FEAT 含「解析/表达式引擎/parse expression」而 US 含「两个/一个/two/one」→ violation） |
| **PRD-S05** | advisory | warn | `semantic_constraints` 非空 | 每个 `SEM-*` id 出现在 **任一** `acceptance_criteria[].description` 或 `requirement_pool[].description` 文本中（V1 **无** `requirement_pool.covers` 字段）；**推荐**用 `REQ-SEM-*` 条目承载 id |
| **PRD-S06** | advisory | warn | `semantic_constraints` 非空 | `prd.md` 须含 `## 语义约束` 且表内 id 与 `prd.json` 一致 |

实现：`validators/prd_semantic_rules.py`（新模块），由 `prd_validate` 节点在 extended rules 之后调用。

### Design 环 — `DES-S01`～`DES-S01b` · `DES-S02`～`DES-S05`

| rule_id | 分级 | 严重度 P2 默认 | 触发 | 判定 |
|---------|------|----------------|------|------|
| **DES-S01** | blocking | error | PRD 有 `SEM-*` | 按 constraint `kind` 应用 §证据规则分支 |
| **DES-S01b** | blocking | error | PRD 有 `one_of:` 维度 | 枚举值在 happy TC 的 `input:`/`request:` 中逐项覆盖 |
| **DES-S02** | advisory | warn | 存在 `ERR-*` 且 when 含格式/输入/input/format | when/message 不得仅含单一示例字面量（启发式：`如.*\d` 且无 operand/operator/操作数 等维度词） |
| **DES-S03** | blocking | error | PRD **任一** constraint 的 `excludes` 非空 | 每个 exclude 有 negative TC；`semantic_evidence.constraint_ref` 或 description 含 exclude.summary 关键词 |
| **DES-S04** | blocking | error | PRD 有 `SEM-*` | `test_cases[].covers` 须含每个 `SEM-*` id |
| **DES-S05** | blocking | error | PRD 有 `kind=input_shape` 的 `SEM-*` | 对应 happy TC 的 `description` 须匹配 `input:` 或 `request:` 前缀 |

**DES-S01～S05 前提：** run 目录 `prd.json` 可加载且含 `semantic_constraints`；若 PRD 无 SEM，设计环语义规则**不触发**（与现网 calculator design 一致）。

实现：`validators/design_semantic_rules.py`（新模块），由 `design_validate` 读取 run 目录 `prd.json` 做交叉校验。

### PRD → design 传导（增补）

| PRD 信号 | design 义务 |
|-----------|-------------|
| 窄触发且 `semantic_constraints[]` 非空 | DES-S01～S05（按 kind 分支） |
| `excludes[]` 非空 | DES-S03 |
| `dimensions` 含 `one_of:` | DES-S01b |
| `SEM-*` id | `test_cases.covers` + `semantic_evidence.constraint_ref` |

写入 `prd-validate.md` 传导表与 `design-validate.md` 依赖说明。

### 双层 enforcement 与流水线行为

语义校验采用 **硬挡流 + 软注入** 双轨，避免「全 warn 则无人修复」：

```text
prd_validate / design_validate
    ├─ blocking 违规 (PRD-S01/S02, DES-S01/S01b/S03/S04/S05)
    │     → severity=error（默认）→ passed=false → 路由回 PM / Architect
    └─ advisory 违规 (PRD-S02b/S03/S04/S05/S06, DES-S02)
          → severity=warn → passed 仍可 true
                ↓
          build_prompt_context 注入 semantic_advisories_*（P2 必做，不依赖 retry）
                ↓
          Architect / Developer / Reviewer 在首轮即看到语义缺口
```

| 机制 | 说明 |
|------|------|
| **blocking** | 契约缺失 / 证据链断裂 — P2 默认 **error**，`graph_routing` 挡流 |
| **advisory** | 启发式质量 — P2 默认 **warn**，不挡流但 **必须** 注入下游 prompt |
| **`semantic_block_on`** | Profile `validation.prd` / `validation.design` 新增字段；默认 **`error`**（与 blocking 缺省一致）。设为 **`warn`** 时 **全部** PRD-S\*/DES-S\* 降为 warn（legacy run / calculator-10-01 回归用） |
| **升 error（advisory）** | P4 prompt 稳定后，将 advisory 表内规则逐条升为 error；或整体设 `semantic_block_on: error` 且 advisory 改分级 |

**与格式规则关系：** `validation.*.block_on` 仍只管 PRD-001～316 / DES-001～224；语义规则单独看 **`semantic_block_on`**（未设则与 `block_on` 相同，但 violation 自带 severity 优先）。

**闭环说明：** P2 起 **blocking 规则即形成 enforcement 闭环**；advisory 靠 prompt 注入补全；P4 后 advisory 升 error 收敛为全硬门禁。

---

## Agent、Prompt 与上下文裁剪

语义门禁为主；prompt 负责**产出契约**；**必须**保证下游能读到 SEM。

### `prompt_context_trim.py`（P1 必改）

下游 Agent **必须**能读到 PRD 语义契约 **与** Design 测试证据；两处裁剪缺一不可：

| 函数 | 必保留字段 | 原因 |
|------|-----------|------|
| **`trim_prd()`** | `semantic_constraints` | Architect / Developer 按 dimensions 实现 |
| **`trim_design(compact=True)`** | `test_cases[]`（限量） | Developer 从 `description` 复制 `input:`/`request:` 字面量写测试 |
| **`trim_retry_bundle()`** | `test_report`、`failure_contexts`（snippet 已在提取阶段预算化，**不**头截断） | 实现环重试；`prd`/`design` 由顶层 `trim_prd` / `trim_design` 处理，**不在** bundle 内 |

**`test_cases` 裁剪规则（compact）：**

- 保留字段：`id`、`kind`、`title`、`description`、`expected`、`covers`、`semantic_evidence`、`steps`
- 列表上限：与现网 `MAX_HEAVY_LIST_ITEMS`（30）一致；超出写 `test_cases_truncated_count`
- **不**截断 `description` 内 `input:`/`request:` 行（整条 TC 保留；必要时只丢 `notes` 等非关键键）

**主动注入（P2，`prompt_context.py`）：**

- 从 `prd_validation` / `design_validation` 提取 rule_id 前缀 `PRD-S` / `DES-S` 的 violations
- **`passed=true` 且仅有 warn 时也注入** — 键名 `semantic_advisories_prd` / `semantic_advisories_design`
- 受众：Architect（prd）、Developer + Reviewer（prd + design）

### PM（`pm.txt` + `LLM_PROMPT_SHAPE`）

- 窄触发时产出 `semantic_constraints[]`；glossary 写语义定义，不用自然语言空格暗示格式。
- 可选：`requirement_pool` 增 `REQ-SEM-*`，description 内嵌 `SEM-IN-1` 等 id，满足 PRD-S05 文本追溯。

### Architect（`architect.txt`）

- PRD 有 `SEM-*` 时，`test_cases` 必填 `semantic_evidence`。
- `covers` 同时含 `AC-*` 与 `SEM-*`。
- `input_shape`：规划等价类（DES-S01）+ `one_of` 逐项覆盖（DES-S01b）。

### Developer（`developer-principles-snippet.txt`）

- 解析层按 `semantic_constraints.dimensions` 实现，不按 AC 第一个示例。
- 测试从 design `description` 复制 `input:` 字面量；覆盖 design 中全部等价类与 `one_of` 枚举。

### Reviewer（`reviewer.txt`，P5）

- 对照 `semantic_constraints` 与 `test_report`：是否只测了一种句法投影。

---

## 可选：P6 `semantic_review` 节点

| 项 | 说明 |
|----|------|
| 位置 | `prd_validate` 之后或 `design_validate` 之后 |
| 输入 | `prd.json` + `design.json`（可选） |
| 输出 | `semantic_review.json`（violations 列表） |
| 默认 | **关闭** |
| 用途 | legacy PRD 的 LLM lint；发现沉淀为 PRD-S/DES-S 硬规则 |

---

## 实施分期

| 阶段 | 交付物 | 验收 |
|------|--------|------|
| **P1** | 本文定稿；`schemas/prd.py` + **`prompt_context_trim.py`**（`semantic_constraints` + compact `test_cases`） | schema 单测；Developer compact context 含 TC |
| **P2** | `prd_semantic_rules.py` + Profile **`semantic_block_on`** + `semantic_advisories_*` 注入 + `prd-validate.md` | blocking 挡流；advisory warn 仍注入 prompt |
| **P3** | `design.py` + `design_semantic_rules.py` + `design-validate.md` | 见 §回归预期（补 SEM 后 design） |
| **P4** | PM/Architect prompt + `prd_md` 渲染 `prd.md` §语义约束 | 新 run 产出 SEM + evidence |
| **P5** | Developer 原则 + Reviewer 补充 | 新 run `1*2` 通过 |
| **P6** | 可选 `semantic_review` | profile 可开关 |

**advisory 升 error 条件：** P4 prompt 稳定后；连续 3 个 profile 任务 semantic warn 为 0，且 golden run 通过。

**Legacy 回归（calculator-10-01）：** Profile 或单次 run 设 `validation.prd.semantic_block_on: warn`（及 design 同理），则 PRD-S01 等 blocking 规则亦以 warn 报告，与 §回归预期一致。

---

## 计算器回归预期（定性）

### 现网 `calculator-10-01`（不修改 run 产物）

**PRD 环**（`prd.json` 无 `semantic_constraints`，窄触发成立；Profile `semantic_block_on: warn`）：

| 规则 | 预期 |
|------|------|
| PRD-S01 | warn — 缺 `semantic_constraints`（默认 profile 为 **error** 挡 PM） |
| PRD-S04 | warn — FEAT「解析表达式」宽于 US「两数一符」 |
| PRD-S03 | warn — scope_out「混合运算」无结构化 excludes |

**Design 环**（PRD 无 SEM，**DES-S01～S05 均不触发**，含 DES-S02）：

| 规则 | 预期 |
|------|------|
| DES-S01 / S01b / S02 / S03 / S04 / S05 | **不触发** — V1 实现仅在 `prd.json` 含非空 `semantic_constraints` 时运行 `design_semantic_rules` |

> legacy `calculator-10-01` design 的 ERR 字面量问题（原 DES-S02 启发式）在 V1 **不单独 lint**；待 PRD 补 SEM 后由 DES-S01/S01b 与 error_catalog prompt 一并收敛。

### 新 run（PM 产出 SEM-IN-1 + Architect 满足 S01/S01b）

| 规则 | 预期 |
|------|------|
| PRD-S* | 无 warn |
| DES-S* | 无 warn |
| 实现（P5 后） | `1*2`、`7 * 8` 均通过；`1+2+3` negative；四则运算符均有 happy TC |

### 对照：补 SEM 后重跑**现网 design.json**（实验用，非交付）

| 规则 | 预期 |
|------|------|
| DES-S01 | warn — 仅一种等价类（缺紧凑/空格变体） |
| DES-S01b | warn — 未逐项覆盖 `one_of` 四运算符 |

---

## 文件变更清单

| 路径 | 变更 |
|------|------|
| `docs/superpowers/specs/2026-07-10-semantic-validation-design.md` | 本文 |
| `docs/design/pipeline/artifact-schemas/prd-spec.md` | 增 `semantic_constraints` |
| `docs/design/pipeline/artifact-schemas/design-spec.md` | 增 `semantic_evidence` + `TestCase` 扩展 |
| `docs/design/pipeline/artifact-templates/prd-spec.md` | 增 `## 语义约束` 写作规范 |
| `docs/design/pipeline/artifact-templates/design-spec.md` | §6 语义证据写作规范 |
| `docs/design/pipeline/quality-gates/prd-validate.md` | 增 §3.4 Semantic + 传导 |
| `docs/design/pipeline/quality-gates/design-validate.md` | 增 §1.7 Semantic |
| `multi_agent_code_factory/schemas/prd.py` | 模型 + `LLM_PROMPT_SHAPE` |
| `multi_agent_code_factory/schemas/design.py` | `SemanticEvidence` + `TestCase` |
| `multi_agent_code_factory/validators/prd_semantic_rules.py` | 新 |
| `multi_agent_code_factory/validators/design_semantic_rules.py` | 新 |
| `multi_agent_code_factory/nodes/prd_validate.py` | 挂载 S 规则 |
| `multi_agent_code_factory/nodes/design_validate.py` | 已读 prd；挂载 S 规则 |
| `multi_agent_code_factory/renderers/prd_md.py` | 渲染语义约束章 |
| **`multi_agent_code_factory/prompt_context_trim.py`** | **`trim_prd` 保留 `semantic_constraints`；`trim_design(compact)` 保留 `test_cases`** |
| **`multi_agent_code_factory/prompt_context.py`** | **注入 `semantic_advisories_*`（warn 亦注入）** |
| **`multi_agent_code_factory/agents/llm/prompt/validation_feedback.py`** | **`format_semantic_advisories()`** |
| `multi_agent_code_factory/profile_config/models.py` | `ValidationGateConfig.semantic_block_on` |
| `profiles/_shared/prompts/pm.txt` | 产出指引 |
| `profiles/_shared/prompts/architect.txt` | evidence 指引 |
| `profiles/_shared/prompts/developer-principles-snippet.txt` | 解析语义原则 |
| `tests/test_prd_semantic_rules.py` | 新 |
| `tests/test_design_semantic_rules.py` | 新 |

---

## 开放问题

1. **`command_shape` dimensions 模板（V2）**：子命令型 CLI 的 `dimensions` 如何表达（`subcommand: one_of:add,list,done`）？V1 不触发窄门禁，可延后。
2. **API JSONPath 级 dimensions（V2）**：嵌套字段计数是否引入 `path:` 前缀？
3. **`requirement_pool.covers`（V2）**：是否增结构化 `covers: string[]`，替代 PRD-S05 文本匹配？
4. **PRD-S03/S04 多语言**：V1 中英启发式；是否 P6 后扩 locale 表？

---

## 参考

- 讨论上下文：`calculator-10-01` — `1*2` 为语义等价类缺失；`1+2+3` 为排除语义未结构化。
- 既有 dev-principles 分层：[`2026-07-09-dev-principles-design.md`](./2026-07-09-dev-principles-design.md)
- 既有 TC id 规则：DES-024 `TC-{HAP|NEG|BND}-{DOMAIN}-\d{3}`
- PRD 产物命名：[`2026-07-10-prd-artifact-rename-design.md`](./2026-07-10-prd-artifact-rename-design.md)
