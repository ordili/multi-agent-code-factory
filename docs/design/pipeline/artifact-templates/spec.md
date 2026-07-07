# spec.md — PM 人读文档格式



> **节点交接以：** [`../artifact-schemas/spec.md`](../artifact-schemas/spec.md)（`SpecArtifact` / `spec.json`）**为准**；本模板为人读渲染目标。  

> **Run 路径：** `docs/runs/<task_id>/spec.md`  

> **校验：** JSON → [quality-gates.md §3](../quality-gates.md#3-spec_validate--规则清单)；MD 格式 → §3.3（P1）



借鉴主流 PRD（功能清单 + 成功指标/KPI + 用户故事 + 验收标准）与 MetaGPT WritePRD；字段与 `SpecArtifact` **一一对应**；**以 `spec.json` 为准**，本模板为渲染目标。



---



## 概念分工



| 概念 | 回答的问题 | JSON 字段 |

|------|------------|-----------|

| **成功指标 / KPI** | 怎样算「做成了」？ | `success_metrics[]` |

| **功能 / Features** | 交付哪些能力？ | `features[]` |

| **用户故事** | 用户怎么用？ | `user_stories[]` |

| **需求池** | 细化条目与优先级？ | `requirement_pool[]` |

| **验收标准 AC** | 流水线怎样判定可交付？ | `acceptance_criteria[]` |
| **稳定性与性能** | 体量、并发、性能 **档位与文字预期**（非具体数值） | `operational_profile` |
| **数据一致性** | 一致性与投递 **模型与文字预期**（非具体数值） | `consistency_profile` |



KPI 偏 **目标与度量**；AC 偏 **可执行验收**（含 `automated_test`）。二者可呼应（如 KPI 引用 AC id），但不互相替代。

### 功能 vs 用户故事 vs 需求池（是否重复？）

**不重复，但层次不同。** 一句话：

| 字段 | 视角 | 粒度 | 典型 id | 给谁用 |
|------|------|------|---------|--------|
| **`features[]`** | 产品 **有什么能力** | 模块 / 能力级 | `FEAT-1` | Architect 拆模块、`design.dev_tasks` |
| **`user_stories[]`** | 用户 **怎么用、为何用** | 场景级 | `US-1` | Developer 理解行为；Reviewer 对场景 |
| **`requirement_pool[]`** | **可排期、可优先级** 的条目 | 条目 / 任务级 | `REQ-1` | 细化实现点；可挂 `feature_id` |

```text
FEAT-1 待办 CRUD
  ├── US-1 添加待办
  ├── US-2 重启后仍能看到列表
  └── REQ-1 持久化到 JSON（feature_id=FEAT-2）
      REQ-2 CLI 子命令解析（feature_id=FEAT-1）
```

**对照（同一件事三种写法）：**

| 功能 | 用户故事 | 需求池 |
|------|----------|--------|
| FEAT-1：待办 CRUD | US-1：As a 用户, I want 添加待办, so that 记录任务 | REQ-2：实现 `add` 子命令与参数校验 |

- **功能** 不写 As a / I want（那是故事句式）。
- **需求池** 可更 **技术/实现向**（存储格式、错误码、边界），且带 **P0/P1** 排序；MetaGPT 的 Requirement Pool 即此层。
- **小任务**（如单文件 CLI）：可 **1 个 FEAT + 2～3 个 US + 1～3 个 REQ**，不必凑数；`requirement_pool` 不得与 `features` 逐字复制（`SPEC-107` warn）。

**最小可行：** 至少各 1 条；若只有单一能力，可 `FEAT-1` 覆盖全局，US 描述主流程，REQ 只列 1～2 条实现细节。

---



## 固定章节（1–10 必填，11 推荐）

| § | Markdown 标题 | 对应 JSON 字段 | 必填 |
|---|---------------|----------------|------|
| — | `# {title}` | `title` | ✓ |
| 1 | `## 概述` | `summary`、`profile`、`revision` | ✓ |
| 2 | `## 背景与上下文` | `context` | ✓ |
| 3 | `## 成功指标` | `success_metrics[]` | ✓ |
| 4 | `## 功能` | `features[]` | ✓ |
| 5 | `## 用户故事` | `user_stories[]` | ✓ |
| 6 | `## 需求池` | `requirement_pool[]` | ✓ |
| 7 | `## 范围` | `scope_in[]`、`scope_out[]` | ✓ |
| 8 | `## 稳定性、性能与数据一致性` | `operational_profile`、`consistency_profile` | ✓ |
| 9 | `## 验收标准` | `acceptance_criteria[]` | ✓ |
| 10 | `## 约束` | `constraints[]` | ✓（无则写「无额外约束」） |
| 11 | `## 待澄清项` | —（仅 MD） | 推荐 |



**页脚元数据（必填，放文末）：**



```markdown

---

task_profile: {profile}

revision: {revision}

parent_task_id: {parent_task_id 或 —}

```



---



## 各节写法



### §1 概述



- 首段：`summary` 原文或略扩写（不超过 3 句）。

- 列表：`Profile`、`Revision`；增量 run 时注明 `Parent task`。



### §2 背景与上下文



- 用表格或 bullet 列出 `context` 键值（如 `language`、`build_tool`、`interface`）。

- `language` 须与 Profile 一致（`SPEC-006`）。



### §3 成功指标



表格推荐列：`ID` | 指标名称 | 说明 | 目标值 | 验证方式



- id 形如 `KPI-1`。

- `target` 须可判断（如「pytest 全绿」「P0 功能手动走通」「延迟 < 200ms」）。

- `verifiable_by`：`manual` | `automated_test` | `deploy_check`（与 AC 同枚举）。



### §4 功能



表格推荐列：`ID` | 功能名 | 描述 | 优先级 | 关联用户故事



- id 形如 `FEAT-1`。

- `priority`：`P0` | `P1` | `P2`（P0 = 本次必须交付）。

- 可选 `user_story_ids` 列：`US-1, US-2`。



### §5 用户故事



表格：`ID` | As a | Want | So that



### §6 需求池



表格：`ID` | 描述 | 优先级 | 关联功能（可选）



- 可选 `feature_id` 指向 `FEAT-*`。



### §7 范围



- **本次包含（scope_in）**

- **明确不做（scope_out）**



### §8 稳定性、性能与数据一致性

本节对应 JSON **`operational_profile`** 与 **`consistency_profile`**（非功能 / 运行态 **基线假设**）。

> **PM 阶段写法（重要）：** 只写 **档位枚举 + 是/否 + 简短文字说明**（如「本地 CLI、无 SLA」「允许秒级读滞后」）。**不要**在 spec 中写具体数值（如 p99、QPS、99.9%、RPO/RTO 秒数、`< 5s` 等）。  
> **量化指标** 由 Architect 在 [`design.md`](./design.md) / `design.json`（如 `non_functional`、模块 SLA、缓存 TTL）中给出，并须 **追溯** 本节档位与说明。

Architect 据此选型：单线程 vs 异步、缓存、连接池、事务边界、幂等等。

#### 8.1 稳定性与性能（`operational_profile`）

**`spec.md` 推荐：一段说明 + 简表（无数字列）**

| 项 | 说明（文字） |
|----|----------------|
| 用户体量 | 选档位 + 一句场景（如「单用户本地 CLI」） |
| 高并发 | 是 / 否 + 一句原因（如「无并行请求」） |
| 性能预期 | 选 `tier` + **文字**（如「交互可感知即可，无 SLA」） |

JSON 映射（PM 阶段）：

| 字段 | PM 填什么 | PM 阶段 **不填** |
|------|-----------|------------------|
| `user_scale` | 枚举 | — |
| `user_scale_notes` | 定性场景描述 | 具体 DAU / 并发数 |
| `high_concurrency` | boolean | — |
| `performance.tier` | 枚举 | — |
| `performance.notes` | **主要** 性能文字说明 | — |
| `performance.latency` / `throughput` / `availability` | — | 留给 design |

**`user_scale` 枚举（含义，非 spec 必填数字）：**

| 值 | 含义 | 文字示例 |
|----|------|----------|
| `personal` | 单用户、本地/CLI | Todo CLI、脚本 |
| `team` | 小团队内部 | 内部工具、小群协作 |
| `multi_tenant` | 多租户或较大规模 | SaaS 单区域 |
| `internet` | 面向公网大规模 | 消费级产品 |

**`performance.tier` 枚举：**

| 值 | 含义 |
|----|------|
| `best_effort` | 功能优先，无 SLA（CLI 默认） |
| `interactive` | 人可感知的交互响应 |
| `low_latency` | 低延迟场景（套利、交易等） |
| `custom` | 非标准；须在 `performance.notes` **文字** 说明，数值进 design |

#### 8.2 数据一致性（`consistency_profile`）

**`spec.md` 推荐：简表（枚举 + 文字说明列）**

| 项 | 说明（文字） |
|----|----------------|
| 一致性模型 | 选档位 + 一句（如「单文件本地，无跨节点同步」） |
| 投递语义 | 选枚举 + 一句（如「写盘尽力不丢，可接受重试」） |
| 多写者 / 须幂等 | 是 / 否 |
| 冲突策略 | 选枚举或「不适用」 |
| 补充说明 | 定性预期（如「重启后数据不丢」）；**不写** RPO/RTO 秒数 |

JSON 映射（PM 阶段）：

| 字段 | PM 填什么 | PM 阶段 **不填** |
|------|-----------|------------------|
| `consistency_model` | 枚举 | — |
| `delivery` | 枚举 | — |
| `multi_writer` / `idempotency_required` | boolean | — |
| `conflict_strategy` | 枚举（多写者时必填） | — |
| `notes` | **主要** 一致性文字说明 | — |
| `staleness_bound` / `recovery` | — | 留给 design |

**`consistency_model` / `delivery` / `conflict_strategy` 枚举** 见 [`schemas/spec.md`](../artifact-schemas/spec.md)（Architect 实现时对照；PM 在 spec.md 用 **中文说明** 即可）。

**与 KPI / 约束 / design 关系：**

| 层级 | 写什么 |
|------|--------|
| **spec §8** | 档位 + 定性说明（本文） |
| **`success_metrics`** | 可判定的 **业务结果**（如「重启后列表不丢」），仍避免写 p99 等工程指标 |
| **`constraints[]`** | 禁止项（如 `no_dual_write_without_reconciliation`） |
| **`design.md`** | 具体 latency、吞吐、可用性、RPO/RTO、缓存滞后等 **数值与方案** |

### §9 验收标准



表格：`ID` | 描述 | 验证方式（`verifiable_by`）



至少一条 `automated_test`（`SPEC-201`，warn）。建议 P0 功能在 AC 或 KPI 中有覆盖（`SPEC-106`，warn）。



### §10 约束



逐条列出 `constraints[]`。



### §11 待澄清项（推荐）



借鉴 MetaGPT `Anything UNCLEAR`；无则写「无」。



---



## 完整示例



```markdown

# CLI Todo App



## 概述



命令行增删查 Todo，数据存本地 JSON。



- **Profile：** default

- **Revision：** 1



## 背景与上下文



| 键 | 值 |

|----|-----|

| language | python |

| build_tool | pip |

| interface | cli |

| storage | json_file |



## 成功指标



| ID | 指标名称 | 说明 | 目标值 | 验证方式 |

|----|----------|------|--------|----------|

| KPI-1 | 核心流程可用 | 增删查与持久化无报错 | 手动走通 3 条 US | manual |

| KPI-2 | 自动化质量 | 回归可重复 | pytest 全绿 | automated_test |



## 功能



| ID | 功能名 | 描述 | 优先级 | 关联用户故事 |

|----|--------|------|--------|--------------|

| FEAT-1 | 待办 CRUD | add/list/done 子命令 | P0 | US-1, US-2 |

| FEAT-2 | 本地持久化 | JSON 文件读写 | P0 | US-2 |



## 用户故事



| ID | As a | Want | So that |

|----|------|------|---------|

| US-1 | 用户 | 添加待办 | 记录任务 |

| US-2 | 用户 | 关闭程序再打开仍能看到列表 | 数据不丢 |



## 需求池



| ID | 描述 | 优先级 | 关联功能 |

|----|------|--------|----------|

| REQ-1 | todos 存于单 JSON 文件 | P0 | FEAT-2 |



## 范围



**本次包含（scope_in）**



- add/list/done 子命令

- 单元测试



**明确不做（scope_out）**



- Web UI

- 多用户



## 稳定性、性能与数据一致性

本地 CLI 工具：单用户、无高并发、功能优先；数据单文件本地持久化，重启后不丢即可。具体延迟、吞吐与 RPO/RTO 见设计文档。

### 稳定性与性能

| 项 | 说明 |
|----|------|
| 用户体量 | personal — 单用户本地 CLI |
| 高并发 | 否 — 无并行请求场景 |
| 性能预期 | best_effort — 交互可感知即可，不设 SLA |

### 数据一致性

| 项 | 说明 |
|----|------|
| 一致性模型 | local_only — 单进程单 JSON，无跨节点同步 |
| 投递语义 | at_least_once — 写盘尽力持久化，进程异常时依赖原子写 |
| 多写者 | 否 |
| 须幂等 | 否 |
| 冲突策略 | 不适用 |
| 补充说明 | 重启后列表与 spec 外数据不丢 |



## 验收标准



| ID | 描述 | 验证方式 |

|----|------|----------|

| AC-1 | 单元测试全部通过 | automated_test |



## 约束



- no_secrets_in_repo



## 待澄清项



无



---

task_profile: default

revision: 1

parent_task_id: —

```



---



## 与 MetaGPT PRD 对照



| MetaGPT（WritePRD） | 本模板 |

|---------------------|--------|

| Product Goals | §1 `summary` + §3 `success_metrics` |

| User Stories | §5 |

| Requirement Pool | §6 |

| Requirement Analysis | 并入 §4 功能描述或 §6 |

| Competitive Analysis / UI draft | **非 MVP**；可选 §10 |

| Anything UNCLEAR | §10 |

| Programming Language | §2 `context.language` |



---



## 实现提示



- 渲染器：`multi_agent_code_factory/renderers/spec_md.py`（P0）。

- HITL：`spec_hitl` 审批人阅读本文件 + `spec_validation.json`。

- 禁止：下游 Agent 仅读 `spec.md` 而不读 `spec.json`。


