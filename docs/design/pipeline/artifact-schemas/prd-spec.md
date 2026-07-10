# prd-spec.md — SpecArtifact（PM JSON 契约）

## 依赖上游文档（只读）

审查 / 修订本文时 **以本表、正文字段定义及同名上游人读 § 映射为准**。`quality-gates/` 为**下游**，不在此表列出（见 [README.md §单向依赖](../README.md#1-单向依赖)）。


| 分类       | 上游文档                                                                | 定位                               |
| -------- | ------------------------------------------------------------------- | -------------------------------- |
| **总设计**  | [multi-agent-pipeline-design.md](../multi-agent-pipeline-design.md) | 系统的总体设计书 |
| **人读模板** | [artifact-templates/prd-spec.md](../artifact-templates/prd-spec.md) | 上游人读 prd-spec.md               |
| **运行配置** | [profiles.md](../profiles.md)                                       | `profile`、`context` 等 Profile 注入字段语境 |


---

> **实现：** `multi_agent_code_factory/schemas/spec.py`  
> **Run 路径：** `docs/runs/<task_id>/spec.json`

机器可读契约以 **本文 + Pydantic** 为准。

---

## 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | `"1"` | 固定 |
| `profile` | string | 与 CLI `--profile` 一致 |
| `revision` | integer | 需求环修订次数，从 1 起 |
| `parent_task_id` | string? | 增量 run 父任务 |
| `title` | string | 任务标题 |
| `summary` | string | 一两句话目标（不展开功能列表） |
| `context` | object | 领域上下文（见 [context](#context)） |
| `success_metrics` | SuccessMetric[] | **业务指标**（可选；无则 `[]`） |
| `features` | FeatureItem[] | 功能清单 |
| `user_stories` | UserStory[] | 用户故事 |
| `requirement_pool` | RequirementItem[] | 需求池 |
| `scope_in` | string[] | 本次边界（非 FEAT 复述） |
| `scope_out` | string[] | 明确不做 |
| `operational_profile` | OperationalProfile | 稳定性 / 性能基线（PM 阶段档位 + 文字） |
| `consistency_profile` | ConsistencyProfile | 数据一致性基线（PM 阶段档位 + 文字） |
| `acceptance_criteria` | AcceptanceCriterion[] | 流水线验收项 |
| `constraints` | string[] | 硬规则，如 `no_secrets_in_repo` |

**分层（与 prd-spec 一致）：** `features` = 能力；`user_stories` = 用户可观察行为；`requirement_pool` = 可排期实现细项；`success_metrics` = 业务结果（可选）；`acceptance_criteria` = 可执行门禁。

---

## context

`context` 为 **可扩展 object**（`dict[str, Any]`）。Profile 可用 `context_schema` 约束额外键。

### 领域键（PRD §3，示例）

| 键 | 说明 |
|----|------|
| `interface` | `cli` / `web` / `api` / `batch` 等 |
| `storage` | `local_file` / `database` / `none` 等 |
| `audience` | `single_user` / `team` 等 |
| `deployment` | `local` / `single_server` / `saas` 等（可选） |

PRD §3 写 **产品形态**；`operational_profile.user_scale` 等写 **运行态假设**（勿与 §3 同义重复展开）。

### `language` / `build_tool`

流水线字段：通常由 **Profile 绑定或 normalizer 注入**（须与 Profile 一致）。**不是** PM 在 `context` 里写的产品形态决策字段。

### `glossary[]`（约定）

术语表；与 prd-spec §2 对应。Pydantic 未单独建模前，作为 `context` 内数组传递。

**GlossaryEntry：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `term` | string | 名词 |
| `definition` | string | 一句话解释 |

```json
"context": {
  "interface": "cli",
  "storage": "none",
  "audience": "single_user",
  "glossary": [
    { "term": "表达式", "definition": "用户输入的算式字符串，由数字、运算符、括号组成" },
    { "term": "CLI 使用者", "definition": "在命令行输入表达式并查看结果的人" }
  ]
}
```

---

## SuccessMetric（业务指标 / KPI）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 如 `KPI-1` |
| `name` | string | 指标名称 |
| `description` | string | 业务结果描述（非「测试通过」类工程指标） |
| `target` | string | 可判定目标；可引用 `US-*` 或 `AC-*` |
| `verifiable_by` | enum | `automated_test` \| `manual` \| `deploy_check` \| `lint` |

**可选：** 小工具 / 目标已在 `summary` + `acceptance_criteria` 说清时，`success_metrics` 可为 `[]`。

**与 AC 分工：** KPI = 做成什么样；AC = 流水线怎么验。勿同义重复。

---

## FeatureItem

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 如 `FEAT-1` |
| `name` | string | 功能名 |
| `description` | string | **能力级**说明（非 Connextra 用户句式） |
| `priority` | enum | `P0` \| `P1` \| `P2` |
| `user_story_ids` | string[]? | 关联 `user_stories[].id`；P0 推荐 ≥1 |

---

## UserStory

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 如 `US-1`；全局唯一 |
| `as_a` | string | 角色 / Persona；优先用 `context.glossary` 中定义的角色 |
| `want` | string | **用户可观察行为**（非实现细节） |
| `so_that` | string | 业务价值 |

LLM 可输出 Connextra 整句；normalizer 可解析为 `{ as_a, want, so_that }`（见 `spec.py` `_USER_STORY_RE`）。

**数量：** 建议 ≥2（主流程 + 边界/异常之一）。异常场景 US **可选**（见 prd-spec §6）。

---

## RequirementItem

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 如 `REQ-1` |
| `description` | string | 可排期 **实现/交付** 细项（非 US 原文复制） |
| `priority` | enum | `P0` \| `P1` \| `P2`（必填） |
| `feature_id` | string? | 关联 `FEAT-*` |
| `depends_on` | string[]? | **约定**：前置 `REQ-*` id；与 design `dev_tasks[].depends_on` 同名异层 |

**优先级 ≠ 开发顺序**；同批 P0 的先后用 `depends_on` 表达。

---

## AcceptanceCriterion

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 如 `AC-1` |
| `description` | string | 可执行验收描述 |
| `verifiable_by` | enum | `automated_test` \| `manual` \| `deploy_check` \| `lint` |

建议至少一条 `automated_test`。每条 P0 US 行为应被 AC 或（若有）KPI manual 项覆盖。

---

## OperationalProfile

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_scale` | enum | `personal` \| `team` \| `multi_tenant` \| `internet` |
| `user_scale_notes` | string? | 定性场景；PM 阶段不写 DAU/并发数 |
| `high_concurrency` | boolean | 是否须支撑高并发 |
| `performance` | PerformanceSpec | 性能档位 |

### PerformanceSpec

| 字段 | 类型 | 说明 |
|------|------|------|
| `tier` | enum | `best_effort` \| `interactive` \| `low_latency` \| `custom` |
| `latency` | string? | **design** 阶段量化；spec 留空 |
| `throughput` | string? | **design** 阶段量化；spec 留空 |
| `availability` | string? | **design** 阶段量化；spec 留空 |
| `notes` | string? | PM 主要性能文字说明；`tier=custom` 时须非空 |

> **PM vs Design：** spec 阶段 PM 填 **枚举 + `notes`**；`latency` / `throughput` / `availability` 等数值字段由 Architect 在 [design.json](./design-spec.md) 的 `non_functional` 填写。

---

## ConsistencyProfile

| 字段 | 类型 | 说明 |
|------|------|------|
| `consistency_model` | enum | `local_only` \| `strong` \| `eventual` \| `session` \| `custom` |
| `delivery` | enum | `best_effort` \| `at_most_once` \| `at_least_once` \| `exactly_once` |
| `multi_writer` | boolean | 是否多写者并发更新同一数据源 |
| `idempotency_required` | boolean | 关键副作用是否须 **重试安全**（≠ 纯函数「确定性」） |
| `conflict_strategy` | enum? | `not_applicable` \| `single_writer` \| `last_write_wins` \| `versioned_merge` \| `manual` |
| `staleness_bound` | string? | design 阶段；spec 留空 |
| `recovery` | object? | design 阶段 `{ "rpo"?, "rto"? }`；spec 留空 |
| `notes` | string? | 一致性文字说明；**不写**功能异常（→ US/REQ/AC） |

**无持久化 / 纯 CLI 默认（`storage: none`）：**

| 字段 | 推荐值 |
|------|--------|
| `consistency_model` | `local_only` |
| `delivery` | `best_effort`（无消息队列；勿用「不适用」非枚举值） |
| `multi_writer` | `false` |
| `idempotency_required` | `false`（确定性写 `notes`，不当作幂等） |
| `conflict_strategy` | `not_applicable` |

---

## 示例（default — CLI 四则运算计算器）

无业务指标、无额外一致性要求时：`success_metrics: []`；`consistency_profile` 用 `local_only` 等 **最小档位**（表示无跨请求/持久化状态，非空对象占位）。

```json
{
  "version": "1",
  "profile": "default",
  "revision": 1,
  "title": "CLI 四则运算计算器",
  "summary": "命令行输入数学表达式，支持加减乘除、括号与小数，输出求值结果。",
  "context": {
    "interface": "cli",
    "storage": "none",
    "audience": "single_user",
    "glossary": [
      { "term": "表达式", "definition": "用户输入的算式字符串，由数字、运算符、括号组成" },
      { "term": "运算符", "definition": "本产品中指 +、-、*、/ 四则运算符号" },
      { "term": "小数", "definition": "含小数点的数值字面量（如 3.14、.5）" },
      { "term": "CLI 使用者", "definition": "在命令行输入表达式并查看结果的人" }
    ]
  },
  "success_metrics": [],
  "features": [
    {
      "id": "FEAT-1",
      "name": "四则运算",
      "description": "支持 +、-、*、/ 及运算符优先级",
      "priority": "P0",
      "user_story_ids": ["US-1", "US-4"]
    },
    {
      "id": "FEAT-2",
      "name": "括号求值",
      "description": "支持 () 改变运算顺序，含嵌套括号",
      "priority": "P0",
      "user_story_ids": ["US-2"]
    },
    {
      "id": "FEAT-3",
      "name": "小数运算",
      "description": "支持小数输入与输出；除法产生小数结果",
      "priority": "P0",
      "user_story_ids": ["US-3"]
    }
  ],
  "user_stories": [
    {
      "id": "US-1",
      "as_a": "CLI 使用者",
      "want": "输入 1+2*3 等四则表达式并得到正确结果",
      "so_that": "快速完成基础计算"
    },
    {
      "id": "US-2",
      "as_a": "CLI 使用者",
      "want": "输入 (1+2)*3 等含括号的表达式并得到正确结果",
      "so_that": "计算需改变优先级的算式"
    },
    {
      "id": "US-3",
      "as_a": "CLI 使用者",
      "want": "输入 3.5/2 等含小数的表达式并得到正确结果",
      "so_that": "处理非整数计算"
    },
    {
      "id": "US-4",
      "as_a": "CLI 使用者",
      "want": "输入 2/0 或非法表达式时看到明确错误提示",
      "so_that": "知道输入有误而非程序崩溃"
    }
  ],
  "requirement_pool": [
    {
      "id": "REQ-1",
      "description": "表达式词法/语法解析（数字、运算符、括号、小数）",
      "priority": "P0",
      "feature_id": "FEAT-1"
    },
    {
      "id": "REQ-2",
      "description": "求值引擎：四则运算与运算符优先级",
      "priority": "P0",
      "feature_id": "FEAT-1",
      "depends_on": ["REQ-1"]
    },
    {
      "id": "REQ-3",
      "description": "括号嵌套求值",
      "priority": "P0",
      "feature_id": "FEAT-2",
      "depends_on": ["REQ-2"]
    },
    {
      "id": "REQ-4",
      "description": "小数解析与除法小数结果处理",
      "priority": "P0",
      "feature_id": "FEAT-3",
      "depends_on": ["REQ-2"]
    },
    {
      "id": "REQ-5",
      "description": "除零与非法表达式错误提示",
      "priority": "P0",
      "feature_id": "FEAT-1",
      "depends_on": ["REQ-2"]
    }
  ],
  "scope_in": ["本地 CLI 表达式求值（单次或 REPL）", "含自动化测试与基本错误处理"],
  "scope_out": ["Web / GUI", "科学函数（sin、sqrt 等）、取模、幂运算", "计算历史持久化"],
  "operational_profile": {
    "user_scale": "personal",
    "user_scale_notes": "个人使用 — 本地 CLI",
    "high_concurrency": false,
    "performance": {
      "tier": "best_effort",
      "notes": "尽力而为 — 交互可感知即可，不设 SLA"
    }
  },
  "consistency_profile": {
    "consistency_model": "local_only",
    "delivery": "best_effort",
    "multi_writer": false,
    "idempotency_required": false,
    "conflict_strategy": "not_applicable",
    "notes": "人读 spec.md 数据一致性为「无」；无跨请求/持久化状态"
  },
  "acceptance_criteria": [
    {
      "id": "AC-1",
      "description": "自动化测试套件全部通过",
      "verifiable_by": "automated_test"
    },
    {
      "id": "AC-2",
      "description": "手动走通 US-1～US-3 典型表达式，且 US-4（如 2/0）有明确错误提示",
      "verifiable_by": "manual"
    }
  ],
  "constraints": []
}
```

---

## 示例（Rust / Solidity context 节选）

Profile 注入 `language` / `build_tool`；领域键与 §9 档位按任务填写。

```json
{
  "context": {
    "language": "rust",
    "build_tool": "cargo",
    "edition": "2021",
    "interface": "cli"
  },
  "success_metrics": [],
  "features": [
    { "id": "FEAT-1", "name": "CLI 入口", "description": "子命令解析", "priority": "P0" }
  ],
  "operational_profile": {
    "user_scale": "personal",
    "high_concurrency": false,
    "performance": { "tier": "best_effort" }
  },
  "consistency_profile": {
    "consistency_model": "local_only",
    "delivery": "best_effort",
    "multi_writer": false,
    "idempotency_required": false,
    "conflict_strategy": "not_applicable"
  },
  "acceptance_criteria": [
    { "id": "AC-1", "description": "cargo test 全部通过", "verifiable_by": "automated_test" }
  ]
}
```

```json
{
  "context": {
    "language": "solidity",
    "build_tool": "foundry",
    "evm_version": "cancun",
    "test_framework": "forge-std"
  },
  "success_metrics": [
    {
      "id": "KPI-1",
      "name": "合约测试",
      "description": "forge test 本地通过",
      "target": "无 failing",
      "verifiable_by": "automated_test"
    }
  ],
  "features": [
    { "id": "FEAT-1", "name": "Vault 存取", "description": "deposit/withdraw", "priority": "P0" }
  ],
  "operational_profile": {
    "user_scale": "team",
    "high_concurrency": false,
    "performance": { "tier": "best_effort", "notes": "链上读 local fork；无 mainnet 压测" }
  },
  "consistency_profile": {
    "consistency_model": "strong",
    "delivery": "exactly_once",
    "multi_writer": false,
    "idempotency_required": true,
    "conflict_strategy": "single_writer",
    "notes": "链上状态以区块确认为准；重入与 nonce 由合约层约束"
  },
  "acceptance_criteria": [
    {
      "id": "AC-1",
      "description": "forge test 全部通过；不含主网部署",
      "verifiable_by": "automated_test"
    }
  ],
  "constraints": ["no_mainnet_rpc_in_tests", "no_private_keys_in_repo"]
}
```

---

## 约定字段与代码差异

| 字段 | 文档 | `schemas/spec.py` |
|------|------|-------------------|
| `context.glossary[]` | ✓ 约定 | 经 `context: dict` 透传；渲染器读取并输出 §2 |
| `requirement_pool[].depends_on` | ✓ 约定 | `RequirementItem.depends_on` |
| `success_metrics` 可选 | ✓ 可 `[]` | 默认 `[]`；校验规则可能仍 warn |

实现跟进前，以 **本文 + prd-spec** 为准。
