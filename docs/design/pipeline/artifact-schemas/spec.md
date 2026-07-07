# SpecArtifact — PM 输出（JSON）



> **实现：** `multi_agent_code_factory/schemas/spec.py`  

> **Run 路径：** `docs/runs/<task_id>/spec.json`  

> **人读格式：** [artifact-templates/spec.md](../artifact-templates/spec.md) → `spec.md`  

> **下游：** 须通过 [spec_validate](../quality-gates.md#3-spec_validate--规则清单)



## 字段



| 字段 | 类型 | 说明 |

|------|------|------|

| `version` | `"1"` | 固定 |

| `profile` | string | 与 CLI `--profile` 一致 |

| `revision` | integer | 需求环修订次数，从 1 起 |

| `parent_task_id` | string? | 增量 run 父任务 |

| `title` | string | 任务标题 |

| `summary` | string | 一两句话目标 |

| `context` | object | 领域上下文（Profile.`context_schema` 可选约束） |

| `success_metrics` | SuccessMetric[] | **成功指标 / KPI**（怎样算做成） |

| `features` | FeatureItem[] | **功能清单**（交付什么能力） |

| `user_stories` | UserStory[] | 用户故事 |

| `requirement_pool` | RequirementItem[] | 需求池（可引用 `feature_id`） |

| `scope_in` | string[] | 本次要做 |

| `scope_out` | string[] | 明确不做 |
| `operational_profile` | OperationalProfile | **稳定性 / 性能基线**（体量、并发、性能） |
| `consistency_profile` | ConsistencyProfile | **数据一致性**（一致性模型、投递语义、冲突处理） |
| `acceptance_criteria` | AcceptanceCriterion[] | 可测试验收项（怎样算可交付） |

| `constraints` | string[] | 如 `no_secrets_in_repo` |



### SuccessMetric



| 字段 | 类型 | 说明 |

|------|------|------|

| `id` | string | 如 `KPI-1` |

| `name` | string | 指标名称 |

| `description` | string | 度量什么、为何重要 |

| `target` | string | 目标值或可判定标准 |

| `verifiable_by` | enum | `automated_test` \| `manual` \| `deploy_check` \| `lint` |



### FeatureItem



| 字段 | 类型 | 说明 |

|------|------|------|

| `id` | string | 如 `FEAT-1` |

| `name` | string | 功能名 |

| `description` | string | 能力说明 |

| `priority` | enum | `P0` \| `P1` \| `P2` |

| `user_story_ids` | string[]? | 关联 `user_stories[].id` |



### AcceptanceCriterion



| 字段 | 类型 | 说明 |

|------|------|------|

| `id` | string | 如 `AC-1` |

| `description` | string | 验收描述 |

| `verifiable_by` | enum | `automated_test` \| `manual` \| `deploy_check` \| `lint` |

### OperationalProfile

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_scale` | enum | `personal` \| `team` \| `multi_tenant` \| `internet` — 用户体量级别 |
| `user_scale_notes` | string? | 数量级补充（如 DAU、并发用户数） |
| `high_concurrency` | boolean | 是否须支撑高并发（多连接/并行请求） |
| `performance` | PerformanceSpec | 性能要求 |

### PerformanceSpec

| 字段 | 类型 | 说明 |
|------|------|------|
| `tier` | enum | `best_effort` \| `interactive` \| `low_latency` \| `custom` |
| `latency` | string? | design 阶段量化（如 `p99 < 200ms`）；spec 阶段留空 |
| `throughput` | string? | design 阶段量化（如 `100 req/s`）；spec 阶段留空 |
| `availability` | string? | design 阶段量化（如 `99.9%`）；spec 阶段留空 |
| `notes` | string? | 补充；`tier=custom` 时 **须** 非空（**文字**说明；具体 latency/throughput 在 design） |

> **PM vs Design：** `spec.json` 阶段 PM 主要填 **枚举 + `notes` 文字**；`latency` / `throughput` / `availability` / `staleness_bound` / `recovery` **留空**，由 Architect 在 `design.json` 量化。见 [artifact-templates/spec.md §8](../artifact-templates/spec.md#8-稳定性性能与数据一致性)。

### ConsistencyProfile

| 字段 | 类型 | 说明 |
|------|------|------|
| `consistency_model` | enum | `local_only` \| `strong` \| `eventual` \| `session` \| `custom` — 读一致性 / 可见性模型 |
| `delivery` | enum | `best_effort` \| `at_most_once` \| `at_least_once` \| `exactly_once` — 写入或消息投递语义 |
| `multi_writer` | boolean | 是否存在多写者并发更新同一数据源 |
| `idempotency_required` | boolean | 关键副作用操作是否须幂等（重试安全） |
| `conflict_strategy` | enum? | `not_applicable` \| `single_writer` \| `last_write_wins` \| `versioned_merge` \| `manual` |
| `staleness_bound` | string? | design 阶段量化；spec 阶段留空 |
| `recovery` | object? | design 阶段 `{ "rpo"?, "rto"? }`；spec 阶段留空 |
| `notes` | string? | 补充；`consistency_model=custom` 时 **必填**（文字；RPO/RTO 等在 design） |

> **PM vs Design：** 同上；`staleness_bound`、`recovery` 数值字段在 design 阶段填写。

### 嵌套类型



- `UserStory`：`{ "id", "as_a", "want", "so_that" }`

- `RequirementItem`：`{ "id", "description", "priority", "feature_id"? }`



**`context` 建议字段：** `language`、`build_tool`、`interface` 等；须与 Profile.`language` 一致。



## 示例（Python / default）



```json

{

  "version": "1",

  "profile": "default",

  "revision": 1,

  "title": "CLI Todo App",

  "summary": "命令行增删查 Todo，数据存本地 JSON",

  "context": {

    "language": "python",

    "build_tool": "pip",

    "interface": "cli",

    "storage": "json_file"

  },

  "success_metrics": [

    {

      "id": "KPI-1",

      "name": "核心流程可用",

      "description": "增删查与持久化无报错",

      "target": "手动走通 US-1、US-2",

      "verifiable_by": "manual"

    },

    {

      "id": "KPI-2",

      "name": "自动化质量",

      "description": "回归测试可重复",

      "target": "pytest 全部通过",

      "verifiable_by": "automated_test"

    }

  ],

  "features": [

    {

      "id": "FEAT-1",

      "name": "待办 CRUD",

      "description": "add/list/done 子命令",

      "priority": "P0",

      "user_story_ids": ["US-1", "US-2"]

    },

    {

      "id": "FEAT-2",

      "name": "本地持久化",

      "description": "JSON 文件读写",

      "priority": "P0",

      "user_story_ids": ["US-2"]

    }

  ],

  "user_stories": [

    { "id": "US-1", "as_a": "用户", "want": "添加待办", "so_that": "记录任务" },

    { "id": "US-2", "as_a": "用户", "want": "重启后仍能看到列表", "so_that": "数据不丢" }

  ],

  "requirement_pool": [

    { "id": "REQ-1", "description": "持久化到 JSON", "priority": "P0", "feature_id": "FEAT-2" }

  ],

  "scope_in": ["add/list/done 子命令", "单元测试"],
  "scope_out": ["Web UI", "多用户"],
  "operational_profile": {
    "user_scale": "personal",
    "user_scale_notes": "单用户本地 CLI",
    "high_concurrency": false,
    "performance": {
      "tier": "best_effort",
      "notes": "无 SLA；本地 JSON IO"
    }
  },
  "consistency_profile": {
    "consistency_model": "local_only",
    "delivery": "at_least_once",
    "multi_writer": false,
    "idempotency_required": false,
    "conflict_strategy": "not_applicable",
    "notes": "单进程单 JSON；依赖原子写 / fsync，无分布式副本"
  },
  "acceptance_criteria": [

    {

      "id": "AC-1",

      "description": "单元测试全部通过",

      "verifiable_by": "automated_test"

    }

  ],

  "constraints": ["no_secrets_in_repo"]

}

```



## 示例（Rust / Solidity context 节选）



```json

{

  "context": {

    "language": "rust",

    "build_tool": "cargo",

    "edition": "2021",

    "interface": "cli"

  },

  "success_metrics": [

    { "id": "KPI-1", "name": "测试通过", "description": "cargo test 绿", "target": "exit 0", "verifiable_by": "automated_test" }

  ],

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
    "delivery": "at_least_once",
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

    { "id": "KPI-1", "name": "合约测试", "description": "forge test 本地通过", "target": "无 failing", "verifiable_by": "automated_test" }

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

    { "id": "AC-1", "description": "forge test 全部通过；不含主网部署", "verifiable_by": "automated_test" }

  ],

  "constraints": ["no_mainnet_rpc_in_tests", "no_private_keys_in_repo"]

}

```


