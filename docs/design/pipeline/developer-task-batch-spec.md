# Developer 分步实现（Task-Batch）— 设计规格

> **日期：** 2026-07-11  
> **状态：** 已实现（v2.1）  
> **触发条件：** Developer **首轮**实现（`impl_retry_count = 0`）且 `design.dev_tasks` 规模超过单次 LLM 可稳定输出的阈值。  
> **关联：** [multi-agent-pipeline-design.md §4.5](./multi-agent-pipeline-design.md#45-节点上下文watch) · [developer-retry-context-spec.md](./developer-retry-context-spec.md)（重试，已实现） · [dev-manifest-spec.md](./artifact-schemas/dev-manifest-spec.md) · [design-spec.md](./artifact-schemas/design-spec.md)（`dev_tasks[]`） · [profiles.md](./profiles.md)（`tests_missing.detector`）

---

## 1. 问题与目标

### 1.1 现状

当前 Developer 节点在 live 模式下 **只调用一次 LLM**，契约要求一次返回 **全部** `source_files` 与 `tasks_completed`：

```text
run_developer()
  └─ invoke_structured(DeveloperLLMOutput)
       └─ apply_developer_output(patch_only = impl_retry_count > 0)
```

`design.dev_tasks[]` 已有 `id` / `path` / `description` / `depends_on`，但仅作为 LLM **申报字段**；**引擎不按 task 调度多轮**。

[developer-retry-context-spec.md](./developer-retry-context-spec.md) 已解决 **重试** 场景的 Token 与 patch 输出；其 §1.4 将「按 dev_tasks 多轮」列为该 spec 的**非目标**，由 **本文** 单独承载。

### 1.2 大项目问题


| 问题           | 现象                        | 后果              |
| ------------ | ------------------------- | --------------- |
| **Output 爆** | 数十～上百文件 × 全文一次 completion | 截断、漏文件、接口不一致    |
| **Input 爆**  | 全量 `design` 一次注入          | prompt 超限、注意力分散 |
| **依赖乱序**     | 未按 `depends_on` 生成        | 引用未实现符号，幻觉接口    |
| **批间悬空**     | 本批引用下一批才写的代码              | 单批无法自洽          |


### 1.3 目标

在 **不改变图路由**（仍 Developer → QA → Reviewer 一轮）的前提下，于 Developer 节点 **内部** 按 `dev_tasks` DAG 分批调用 LLM：每批 **窄输入 + 小输出**，引擎 merge 写盘并累积 `dev_manifest`。

### 1.4 核心约束（评审必达）


| 约束               | 含义                                                                           | 保证方            |
| ---------------- | ---------------------------------------------------------------------------- | -------------- |
| **C1 顺序正确**      | 全局执行序是 `depends_on` 的 **合法拓扑序**；后继 task 在前置完成前 **不得** 入批                     | Plan 来源 + 静态调度 |
| **C2 批内自闭环（结构）** | 每批 LLM 调用在 **文件与依赖层面** 可独立完成：依赖已满足、`required_paths` 齐全、本批 `covers` 对应测试路径已映射 | 闭包展开 + 引擎门禁    |


**C2 边界（重要）：** 自闭环指 **结构闭包**（该写的源码/测试 **路径** 齐、上游可读），**不**保证批内测试已通过或可通过编译；行为验证仍由 **整轮结束后一次 QA** 完成（见 §3 B4 权衡）。

### 1.5 非目标

- **图级** Developer → micro-QA → Developer 循环
- LLM **自主** `read_file` Tool 拉库（首期由引擎预读 + 摘要注入）
- 替代 Architect 拆 task
- 重试路径改造（[developer-retry-context-spec.md](./developer-retry-context-spec.md)）
- partial 续跑时从中间 batch 恢复（P2，见 §11.2）

---

## 2. 方案总览

```text
design.dev_tasks[] + depends_on
        │
        ▼
  dev_task_scheduler ──► batches[]（静态有序执行计划）
        │
        ├─ batch 1 ──► 门禁 ──► LLM（task_batch）──► patch 写盘 ──┐
        ├─ batch 2 ──► 门禁 ──► LLM ──► patch 写盘 ────────────────┤ merge manifest
        └─ batch N ──► 门禁 ──► LLM ──► patch 写盘 ────────────────┘
        │
        ▼
  dev_manifest.json → QA（一次）→ Reviewer
```

---

## 3. 定稿决策


| #       | 决策           | 结论                                                                                      |
| ------- | ------------ | --------------------------------------------------------------------------------------- |
| **B0**  | Plan List 来源 | **Architect** → `design.dev_tasks[]`；**引擎** → `batches[]`；Developer LLM **不**生成或重排 Plan |
| **B1**  | 分批输出         | 每批 **至少** 交付 `required_paths`；可额外 ≤ `max_extra_output_paths` 辅助文件；禁止重发未改动文件 |
| **B2**  | 调度方          | **引擎** 静态生成 `batches[]`；LLM 不决定顺序                                                       |
| **B3**  | 分批粒度         | 默认 **每批 1 个 dev_task**；多 task 同批仅当 `can_batch_together`（§6.2）                           |
| **B4**  | 批间 QA        | **不** 做；整轮一次 QA（**已知权衡：** 缺陷可能晚至末批 QA 才暴露）                                              |
| **B5**  | `impl_mode`  | `initial` | `task_batch` | `retry_patch`（判定见下）                                          |
| **B6**  | 启用条件         | `len(dev_tasks) > threshold` 或 `FactoryConfig.task_batch.enabled`                       |
| **B7**  | 依赖摘要         | 引擎 `read_file` + `dependency_extract`（按语言 Tier）                                         |
| **B8**  | 预算           | 每批 1 次 `used_llm_calls`；触顶 → partial manifest + `WARN`                                  |
| **B9**  | 五语言          | 调度/merge 语言无关；签名提取按 Tier（与 retry spec 对齐）                                               |
| **B10** | 结构闭包         | `expand_task_closure` + 双阶段门禁（§8）                                                       |
| **B11** | 顺序确定性        | **Kahn** + `task.id` 字典序 tie-break；同输入 → 同 `batches[]`                                  |
| **B12** | 体积预算         | 文件数 + **行数** 双阈值（§5.4）；与 retry `SNIPPET_MAX_TOTAL_LINES`（2000）量级对齐                      |


### 3.1 `impl_mode` 判定


| 场景    | `impl_retry_count` | `impl_mode`   | LLM 次数         | 输出契约                   |
| ----- | ------------------ | ------------- | -------------- | ---------------------- |
| 小项目首轮 | 0                  | `initial`     | 1              | 全量 `source_files`      |
| 大项目首轮 | 0                  | `task_batch`  | `len(batches)` | 每批 patch               |
| 实现环重试 | > 0                | `retry_patch` | 1              | patch + `retry_bundle` |


```python
if impl_retry_count > 0:
    impl_mode = "retry_patch"
elif should_task_batch(design, factory_config):
    impl_mode = "task_batch"
else:
    impl_mode = "initial"
```

默认 `should_task_batch`：`len(design.dev_tasks) > TASK_BATCH_THRESHOLD`（**5**）。

---

## 4. Plan List：来源、顺序与上游契约

### 4.1 两层 Plan

```text
┌──────────────────────────────────────────────────────────────┐
│ 语义 Plan（Architect）                                         │
│  design.dev_tasks[] + file_plan + test_cases                  │
│  门禁: design_validate（DES-001～005）                          │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────┐
│ 执行 Plan（引擎 dev_task_scheduler）                           │
│  batches[]: 静态有序列表，项 = TaskBatch + required_paths      │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
                      Developer LLM（仅实现当前批）
```


| 角色                     | 负责                                           | 不负责                |
| ---------------------- | -------------------------------------------- | ------------------ |
| **Architect**          | 拆分 task、`depends_on`、`covers`、对齐 `file_plan` | LLM 调用次数与 batch 划分 |
| **design_validate**    | 图合法（无环、引用存在）                                 | 排序                 |
| **dev_task_scheduler** | 静态生成 `batches[]`                             | 创造新 task           |
| **Developer LLM**      | 实现 `active_dev_tasks`                        | 生成/重排 Plan         |


### 4.2 顺序正确性（C1）— 三道门禁


| 层级            | 机制                                                        | 失败行为          |
| ------------- | --------------------------------------------------------- | ------------- |
| **G1 设计图合法**  | `DES-005` 无环；`depends_on` 引用已存在 id                        | 不进 Developer  |
| **G2 静态调度合法** | Kahn：batch 序为拓扑序；batch[i] 的 deps 仅依赖 batch[0..i-1] 中 task | 调度器 fail fast |
| **G3 执行单调**   | 运行时 `manifest.tasks_completed` 只增；已完成 task 不再入批           | 引擎断言          |


**稳定排序：** 同拓扑层按 `task.id` 字典序；默认单 task 一批（B3）。

### 4.3 静态规划 vs 运行时消费


| 阶段             | 行为                                                                                       |
| -------------- | ---------------------------------------------------------------------------------------- |
| **规划（节点入口一次）** | `batches = schedule(design)`，基于 DAG **假设各批均成功**；不依赖 `tasks_completed`                    |
| **消费（批循环）**    | 按 `batches[0..N]` 顺序执行；每批前 **`refresh_batch_runtime`** 按当前写盘刷新 `dependency_paths`，再用 **当前** `manifest.tasks_completed` 做 `validate_batch_closure` |


首轮 `tasks_completed=∅` 时，静态序与运行时序一致。**partial 续跑**（budget 触顶后 `continue`）为 P2，需用 `batches_completed` 跳过已消费批（§11.2）。

### 4.4 Architect 上游最低要求（C1/C2 前提）

Architect 产出的 `design.dev_tasks[]` **必须**满足（否则闭包/顺序无法保证）：


| 要求        | 说明                                                                    | 校验                      |
| --------- | --------------------------------------------------------------------- | ----------------------- |
| **依赖完整**  | 引用其他 task 产物的 task，`depends_on` 列出全部前置 id                             | 人工 + Reviewer；引擎不推断隐含依赖 |
| **路径稳定**  | 每 task 有唯一 `path`；与 `file_plan` 主路径一致                                 | DES-003                 |
| **覆盖可追溯** | P0 实现 task 的 `covers[]` 非空，且能在 `test_cases` 中找到 `covers` 交集           | DES 语义规则（warn/error 可配） |
| **首批脚手架** | `pyproject.toml` / `go.mod` 等由 **显式 dev_task** 或 `file_plan` 声明，不默认猜测 | `expand_task_closure`   |
| **测试可映射** | 每个需测 task 的 `covers` 能映射到 §7.2 测试路径规则                                 | 闭包门禁 `tests mapped`     |
| **单 task 体积** | 展开后 `len(required_paths) ≤ max_files_per_batch - max_extra_output_paths`（默认 6）；单实现文件建议 ≤ `max_lines_per_file_hint`（默认 400 行） | 调度 `files_budget`；Reviewer/Architect 人工对照 |
| **超大 task 须拆** | 单 task 闭包若触达行数预算（§5.4 `lines_budget`），Architect 应拆为多个 `depends_on` 串联的 dev_task | 调度 fail → 回 Architect |


**说明：** 引擎 **不**自动拆 task；超限时 fail-fast 并提示缩小 `dev_tasks` 粒度。

---

## 5. Schema

### 5.1 `TaskBatch`（执行计划单元）

```python
class TaskBatch(BaseModel):
    index: int                          # 0-based，全局顺序
    task_ids: list[str]                 # 本批 dev_task id，默认长度 1
    required_paths: list[str]           # 结构闭包：本批必须产出的路径
    dependency_paths: list[str]         # 须注入 dependency_artifacts 的已存在路径
    relevant_test_case_ids: list[str]   # 来自 design.test_cases 切片
    estimated_output_lines: int | None = None  # 调度时按 required_paths 行数估算（已写盘读盘 + 新文件 hint）
```

### 5.2 `ImplBatch`（prompt 注入）

```python
class DependencyArtifact(BaseModel):
    path: str
    kind: Literal["signature_stub", "module_header"]
    line_start: int
    line_end: int
    content: str

class ImplBatch(BaseModel):
    pass_index: int                     # = TaskBatch.index + 1（1-based 展示）
    pass_total: int                     # = len(batches)
    active_dev_tasks: list[DevTask]      # 完整 task 对象（非仅 id）
    completed_dev_tasks: list[str]       # 已完成 id
    required_paths: list[str]           # 与 TaskBatch 相同（prompt/校验共用）
    dependency_artifacts: list[DependencyArtifact]
    relevant_test_cases: list[TestCase]  # 裁剪后
    omitted_dependencies: list[dict]     # 读盘失败等
    closure_note: str                    # 固定提示语
```

### 5.3 `TaskBatchConfig`（`FactoryConfig` / Profile 可覆盖）

```python
class TaskBatchConfig(BaseModel):
    enabled: bool = False
    threshold: int = 5                  # TASK_BATCH_THRESHOLD
    max_tasks_per_batch: int = 1
    max_files_per_batch: int = 8
    max_extra_output_paths: int = 2     # 允许超出 required_paths 的辅助文件数
    max_lines_per_file_hint: int = 400  # Architect 单文件建议上限（设计指引）
    max_output_lines_per_batch: int = 2000   # 本批 completion 行数预算（与 retry SNIPPET_MAX_TOTAL_LINES 对齐）
    max_input_lines_per_batch: int = 2500    # 本批 prompt 注入正文行数预算（含 dependency_artifacts）
    dep_snippet_lines: int = 60
    require_tests: bool = True          # covers 非空 → 必须映射测试路径
```

### 5.4 体积预算常量与估算


| 常量 | 默认 | 用途 |
|------|------|------|
| `max_files_per_batch` | 8 | 单批 `source_files` **合计**上限（含 `paths_extra`） |
| `max_extra_output_paths` | 2 | 输出允许比 `required_paths` **多** 的路径数（如 `__init__.py` 补写） |
| `max_required_paths_per_batch` | *派生* | `max_files_per_batch - max_extra_output_paths`（默认 **6**）；`required_paths` 上限 |
| `max_lines_per_file_hint` | 400 | Architect 设计指引；单文件 **建议** 行数 |
| `max_output_lines_per_batch` | 2000 | 本批 **completion** 合计行数上限（`sum(len(content.splitlines()))`） |
| `max_input_lines_per_batch` | 2500 | 本批 **prompt** 注入合计行数上限 |

**文件数恒等式（默认 6+2=8）：** `len(required_paths) ≤ max_required_paths_per_batch`；`len(output_paths) ≤ max_files_per_batch`；`len(output_paths - required_paths) ≤ max_extra_output_paths`。

**`estimated_output_lines`（调度时）：**

```text
for path in required_paths:
    if path 已写盘: += line_count(read_file(path))
    else: += max_lines_per_file_hint   # 新文件按 hint 估算
```

若 `estimated_output_lines > max_output_lines_per_batch` → 调度 **fail**（`batch_lines_budget_exceeded`），不回 LLM。

**与批数的关系：** 体积预算约束 **单批**；批数仍由 task 数与 `max_tasks_per_batch` 决定。大项目应通过 **更多、更小的 dev_task** 满足行数预算，而非增大单批。

---

## 6. 调度（`dev_task_scheduler`）

### 6.1 算法（Kahn 静态规划）

```text
1. 校验无环（DES-005；运行时双检）
2. Kahn 拓扑排序得 task 序 [t1, t2, ..., tn]
3. 按序遍历每个 task：
     a. 默认单独成批（max_tasks_per_batch=1）
     b. expand_task_closure(task) → required_paths, dependency_paths, test_case_ids
     c. 若 len(required_paths) > max_files_per_batch - max_extra_output_paths → fail（batch_files_budget_exceeded）
     d. 估算 estimated_output_lines；若 > max_output_lines_per_batch → fail（batch_lines_budget_exceeded）
     e. 推入 batches[]
4. 返回 batches[]（完整有序执行计划）
```

### 6.2 `can_batch_together`（可选，首期可不实现）

仅当 `max_tasks_per_batch > 1` 时启用：

```python
def can_batch_together(tasks: list[DevTask]) -> bool:
    # 1. 两两无 depends_on 关系（同一拓扑层）
    # 2. 合并 expand_task_closure 后 len(required_paths) ≤ max_files_per_batch - max_extra_output_paths
    # 3. relevant_test_case_ids 无冲突
```

**首期倾向：** 仅实现 `max_tasks_per_batch=1`。

### 6.3 与 `file_plan` 的关系

- **主路径：** `dev_task.path` 为闭包核心。
- **辅助：** `file_plan` 中路径纳入闭包，规则见 §7.1 `file_plan_aux_paths`。
- **DES-104：** 进入 Developer 前 `file_plan[].path` 须 **等于** 某 `dev_tasks[].path`（[design-validate DES-104](./quality-gates/design-validate.md#11-任务与模块)）；闭包 **不**引入非 `dev_task.path` 的 `file_plan` 项。

---

## 7. 批内闭包（C2）— `expand_task_closure`

### 7.1 `required_paths` 展开规则

```text
required_paths(task) =
    { task.path }
  ∪ file_plan_aux_paths(task)
  ∪ test_paths(task)
```


| 组成                        | 规则                                                                                                             |
| ------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **实现文件**                  | `task.path`                                                                                                    |
| `**file_plan_aux_paths**` | `file_plan` 中满足任一：`path == task.path`；或 `dirname(path) == dirname(task.path)`；或 `file_plan.reason` 含 `task.id` |
| `**test_paths**`          | 见 §7.2                                                                                                         |
| **禁止前向引用**                | `required_paths` 不得含 **其他未完成 task** 的实现文件（测试路径除外）                                                              |

**与 DES-104 / 附录 C 对齐：**

- `file_plan_aux_paths` **仅筛选** `file_plan` 中已存在的路径；因 DES-104，每条入选 path **必须已是** 某个 `dev_tasks[].path`（通常为 **本批 task** 的 `path`，或同批多 task 时其它 task 的 `path`）。
- **不**因「同目录」把 **未**列入 `file_plan`、也 **非**任何 `dev_task.path` 的文件（如仅写在 T1 `description` 里的 `src/__init__.py`）塞进 `required_paths`。
- 此类辅助文件由 Developer 经 §8.2 `paths_extra` 补写（≤ `max_extra_output_paths`），**不计入** `required_paths`。

**示例（Todo CLI，与 [附录 C 执行计划](../artifact-templates/design-spec.md#附录-c-执行计划) 一致）：**


| Batch | task | `required_paths` |
| ----- | ---- | ---------------- |
| 1 | T1 框架 | `pyproject.toml` |
| 2 | T2 store | `src/todo_store.py` |
| 3 | T3 cli | `src/cli.py` |
| 4 | T4 测试 | `tests/test_todo.py` |

（`src/__init__.py` 等由 T1 步 `description` + 批内 `paths_extra` 交付，**不**单独占 `required_paths`。）


### 7.2 `test_paths` 映射（链接 Profile）

当 `task.covers` 非空且 `require_tests=true`：

1. 取 `design.test_cases` 中 `covers ∩ task.covers ≠ ∅` 的条目。
2. 按 `profile.tests_missing.detector` 映射默认测试路径：


| detector                   | 规则                                                                                         |
| -------------------------- | ------------------------------------------------------------------------------------------ |
| `file_stem`（Python/Java 等） | `tests/test_{stem(task.path)}.py` 或 `src/test/java/**/{Class}Test.java`（按 `task.path` 扩展名） |
| `go`                       | `{dirname(task.path)}/{stem}_test.go` 或 `tests/{stem}_test.go`（与 `tests_missing` 一致）       |
| `rust`                     | `tests/{stem}.rs` 或 task.path 内 `#[cfg(test)]`（`inline_tests=true` 时闭包可不生成外部测试路径）          |
| `solidity`                 | `test/{Contract}.t.sol`（stem 来自 `task.path` 的 `.sol` 基名）                                   |


1. 若 `test_cases` 的 `steps` / `description` 显式写出路径，**优先**采用显式路径。
2. 映射失败 → `validate_batch_closure` **失败**（不调用 LLM）。

### 7.3 `dependency_paths` 与 `dependency_artifacts`

- `dependency_paths` = ⋃_{d ∈ task.depends_on} paths(expand_task_closure(d)) 中 **已写盘** 的实现文件。
- 引擎 `read_file` + `dependency_extract`（§9.2）生成 `dependency_artifacts`。
- 读盘失败 → `omitted_dependencies`；若该路径为硬依赖 → 闭包门禁失败。

---

## 8. 门禁（双阶段，唯一权威）

> §7（输出契约）**不重复**本节；实现以本节为准。

### 8.1 `validate_batch_closure`（调用 LLM **之前**）


| 检查               | 说明                                                                     |
| ---------------- | ---------------------------------------------------------------------- |
| `deps_satisfied` | `batch.task_ids` 的 `depends_on ⊆ manifest.tasks_completed`             |
| `deps_readable`  | 每个 `dependency_path` 可读，或列入本批 `required_paths`                         |
| `tests_mapped`   | `require_tests` 且 `covers` 非空 → `required_paths` 含测试路径或 `inline_tests` |
| `files_budget`   | `len(required_paths) ≤ max_files_per_batch - max_extra_output_paths`（§5.4，默认 ≤6） |
| `lines_budget`   | `estimated_output_lines ≤ max_output_lines_per_batch`（§5.4）            |
| `input_budget`   | 组装 prompt 后 `count_context_lines(context) ≤ max_input_lines_per_batch` |

失败 → 记录 `batch_closure_error`；**不调用 LLM**；Developer 节点 fail。

### 8.2 `validate_batch_output`（invoke **之后**，apply **之前**）


| 检查                | 说明                                                                 |
| ----------------- | ------------------------------------------------------------------ |
| `tasks_done`      | `output.tasks_completed` ⊇ `batch.task_ids`                        |
| `paths_complete`  | `output_paths` ⊇ `batch.required_paths`（**允许超集，见下**）                  |
| `paths_extra`     | `len(output_paths - required_paths) ≤ max_extra_output_paths`；额外路径宜为同目录辅助文件（`__init__.py` 等），**无须**是 `dev_task.path` |
| `files_budget`    | `len(output.source_files) ≤ max_files_per_batch`（默认 8，**含** `paths_extra`） |
| `output_lines`    | `sum(line_count(sf.content)) ≤ max_output_lines_per_batch`         |
| `per_file_lines`  | 单文件 `line_count ≤ max_lines_per_file_hint * 2`（硬拒收极端巨型单文件）        |
| `paths_safe`      | 路径不逃逸 `code_root`                                                  |
| `no_forward_stub` | 前向符号引用（首期 **warn**；Q6 决定是否硬拒）                                      |

**`paths_complete` 与超集：** 不要求 `output_paths == required_paths`。最小集合必须齐全；`len(output_paths) ≤ max_files_per_batch` 且额外文件 ≤ `max_extra_output_paths`（与 §5.4 恒等式一致）。同目录辅助路径首期可 warn-only。

失败 → 本批 LLM **重试 1 次**（`format_llm_parse_retry_feedback` / 闭包提示）；仍失败 → 节点异常，保留已成功批。

---

## 9. Prompt 上下文

### 9.1 顶层（每批）


| 字段             | 内容                                                                                        |
| -------------- | ----------------------------------------------------------------------------------------- |
| `prd`          | `trim_prd`                                                                                |
| `design`       | `trim_design_for_task_batch`（§9.1.1）                                                      |
| `profile`      | 与现一致                                                                                      |
| `impl_mode`    | `task_batch`                                                                              |
| `impl_batch`   | `ImplBatch`（§5.2）                                                                         |
| `dev_manifest` | 累积 manifest                                                                               |
| `semantic_advisories_*` | 与现 Developer 相同（若有）                                                          |

**不注入：** 全量无关 `test_cases` / `file_plan` / 无关 `dev_tasks` 正文。

### 9.1.1 `trim_design_for_task_batch(design, batch)`

在 `trim_design(compact=True)` 基础上 **按批过滤**（`prompt_context_trim.py`）：

| 字段 | 保留规则 |
|------|----------|
| `version`, `spec_ref`, `revision`, `summary` | 全量保留 |
| `design_goals`, `non_goals` | 全量保留（通常较短） |
| `dev_tasks` | **仅** `active_dev_tasks` + `completed_dev_tasks` 的 id/path/description/depends_on/covers |
| `modules` | 与 `active_dev_tasks[].path` 模块前缀匹配者 |
| `interfaces` | 被 active task `description` 或 `relevant_test_cases` 提及者；或模块匹配 |
| `file_plan` | `path ∈ batch.required_paths` 或 `file_plan_aux_paths(active)` |
| `test_cases` | `id ∈ batch.relevant_test_case_ids`（`_TEST_CASE_KEEP` 字段子集） |
| `external_dependencies`, `error_catalog` | 全量保留（compact 字段集内） |
| `architecture`, `context_view`, `diagrams` | 可选省略或仅 `summary` 级（超 input 预算时优先裁） |

列表超长时沿用 `_cap_list_items` / `test_cases_truncated_count` 惯例。

### 9.1.2 Input 行数预算（`input_budget`）

计入 `max_input_lines_per_batch` 的正文：

| 来源 | 计入方式 |
|------|----------|
| `trim_prd` | JSON 序列化行数 |
| `trim_design_for_task_batch` | 同上 |
| `impl_batch` | `required_paths`、`dependency_artifacts.content`、`relevant_test_cases` |
| `dev_manifest` | 仅 `tasks_completed` + `changed_files` 摘要（不注入历史源码） |

超预算 → 先 `fit_task_batch_context_to_input_budget` 裁 `diagrams` / `architecture` / `relevant_test_cases`；仍超限则 §8.1 `input_budget` 失败。

### 9.2 `dependency_artifacts` 提取（按语言 Tier）


| Tier | 语言           | 策略                                   |
| ---- | ------------ | ------------------------------------ |
| A    | Python       | AST：public 类/函数签名                    |
| B    | Java/Rust/Go | 导出符号启发式 → 失败则文件头 `dep_snippet_lines` |
| C    | Solidity     | 合约名 + `function`/`event` 行           |


### 9.3 `developer.txt` 补充（`impl_mode=task_batch`）

- 仅实现 `impl_batch.active_dev_tasks`
- **一次交付** `impl_batch.required_paths` 全部文件（可额外 ≤ `max_extra_output_paths` 个同目录辅助文件）
- 不得依赖后续批次才会创建的文件
- 单文件避免超过约 `max_lines_per_file_hint` 行；超长逻辑拆到多个 dev_task（由 Architect 预先拆分）

### 9.4 `extra_system`

与现 Developer 相同：注入 `format_semantic_advisories`（若有）；**不**注入 `format_qa_retry_feedback`（仅 `retry_patch`）。

---

## 10. 输出与 Manifest 合并

### 10.1 `DeveloperLLMOutput`（schema 不变）

```json
{
  "tasks_completed": ["T2"],
  "source_files": [
    { "path": "src/todo_store.py", "content": "..." },
    { "path": "tests/test_todo_store.py", "content": "..." }
  ],
  "notes": "batch 2/5"
}
```


| 字段                | 语义                          |
| ----------------- | --------------------------- |
| `tasks_completed` | **本批**新完成 id（引擎并入 manifest） |
| `source_files`    | **⊇ `required_paths`**；`len` ≤ `max_files_per_batch`（默认 8，含 ≤ `max_extra_output_paths` 条额外路径） |

**路径：** 以 `required_paths` 为最小集；额外路径 ≤ `max_extra_output_paths`（§8.2 `paths_extra`）。

**体积：** 每文件建议 ≤ `max_lines_per_file_hint` 行；硬上限 `max_lines_per_file_hint * 2` / 批合计 `max_output_lines_per_batch`。


### 10.2 Merge

```text
manifest.tasks_completed = union(prev, batch.tasks_completed)
manifest.changed_files   = merge_by_path(prev, batch.changed_files)
```

写盘使用 `apply_developer_output(..., patch_only=True)`。整轮结束写 **一次** `dev_manifest.json`。

---

## 11. 节点控制流与失败策略

```text
run_developer():
  if impl_mode == "initial": ...
  if impl_mode == "retry_patch": ...

  batches = schedule(design)                    # 静态一次
  manifest = state.dev_manifest or empty
  for batch in batches:
      validate_batch_closure(batch, manifest) # §8.1
      check_llm_budget()
      output = invoke_structured(build_task_batch_context(batch, manifest))
      validate_batch_output(output, batch)    # §8.2
      manifest = merge(manifest, apply(..., patch_only=True))
      if budget exhausted: WARN; break
  return manifest
```

### 11.1 失败策略


| 类型         | 行为                                                |
| ---------- | ------------------------------------------------- |
| 闭包失败（§8.1） | 不调 LLM；节点 fail                                    |
| 输出失败（§8.2） | 同批重试 1 次；仍失败 → 节点 fail，保留已成功批                     |
| Budget 触顶  | partial manifest + `WARN`                         |
| QA 失败      | `retry_patch` + `retry_bundle`；**不**重跑 task_batch |


### 11.2 Partial 续跑（P2，本期不实现）

- `dev_manifest` 增加 `batches_completed: int` 或 `notes` 记录最后成功 `batch.index`。
- `continue` 时跳过 `batches[0..k]`，从 `k+1` 消费；`tasks_completed` 从 manifest 水合。
- 详见 [artifact-continue-design.md](./artifact-continue-design.md) 扩展。

---

## 12. 与 retry spec 的关系


| 维度   | task_batch（本文）          | retry_patch（已实现）       |
| ---- | ----------------------- | ---------------------- |
| 触发   | 首轮、task 多               | `impl_retry_count > 0` |
| 输入   | `impl_batch` + 窄 design | `failure_contexts`     |
| 输出   | 本批 patch                | 修复 patch               |
| Plan | 静态 `batches[]`          | 无 batch，最小修复           |


---

## 13. 模块落点


| 模块                                 | 职责                                              |
| ---------------------------------- | ----------------------------------------------- |
| `schemas/task_batch.py`            | `TaskBatch`, `ImplBatch`, `TaskBatchConfig`     |
| `dev_task_scheduler.py`            | Kahn、`expand_task_closure`、`refresh_batch_runtime`、`schedule()` |
| `batch_closure.py`                 | §8 双阶段门禁                                        |
| `dependency_extract.py`            | `dependency_artifacts`                          |
| `prompt_context.py`                | `should_task_batch`, `build_task_batch_context` |
| `agents/developer.py`              | `impl_mode` 三分支 + 批循环                           |
| `agents/developer_output.py`       | `merge_manifest`                                |
| `prompt_context_trim.py`           | `trim_design_for_task_batch`                    |
| `task_batch_context.py`            | `fit_task_batch_context_to_input_budget`        |
| `profiles/*/prompts/developer.txt` | `task_batch` 段落                                 |


---

## 14. 实施分期


| 阶段      | 交付                                                    |
| ------- | ----------------------------------------------------- |
| **TB0** | `TaskBatchConfig` + `impl_mode` 骨架                    |
| **TB1** | `dev_task_scheduler` + 闭包展开 + 单测                      |
| **TB2** | §8 门禁 + `batch_closure.py`                            |
| **TB3** | `impl_batch` prompt + `trim_design` + `developer.txt` |
| **TB4** | `developer.py` 批循环 + merge + budget                   |
| **TB5** | 五语言 `test_paths` 映射 + 文档同步                            |


---

## 15. 测试与验收


| ID     | 场景         | 断言                                     |
| ------ | ---------- | -------------------------------------- |
| TB-T1  | threshold  | ≤5 tasks → `initial`；>5 → `task_batch` |
| TB-T2  | 静态拓扑序      | 乱序输入 → 确定性 `batches[]`                 |
| TB-T2b | 链式依赖       | T1→T2→T3 → 三批顺序 [T1],[T2],[T3]         |
| TB-T3  | 结构闭包       | `source_files` 路径 ⊇ `required_paths`   |
| TB-T3b | 缺测试拒收      | `covers` 非空但无测试路径 → §8.1 `tests_mapped` 失败 |
| TB-T3c | 行数预算（调度）   | `estimated_output_lines > max_output_lines_per_batch` → 调度 fail |
| TB-T3d | 输出行数       | 单批 completion 超 `max_output_lines_per_batch` → §8.2 拒收 |
| TB-T3e | 额外路径       | 超 `max_extra_output_paths` → §8.2 `paths_extra` 拒收 |
| TB-T4  | 依赖摘要       | 后批 `dependency_artifacts` 含前批产出        |
| TB-T5  | patch      | 后批不重写前批未列出文件                           |
| TB-T6  | budget 触顶  | partial manifest                       |
| TB-T7  | QA 后重试     | `retry_patch`，非 task_batch             |
| TB-T8  | test_paths | Python `file_stem` 映射正确                |


---

## 16. 开放问题


| #      | 问题                    | 状态                                        |
| ------ | --------------------- | ----------------------------------------- |
| ~~Q1~~ | `MAX_TASKS_PER_BATCH` | **已闭合：1**（B3）                             |
| ~~Q2~~ | 批内是否必须带测试             | **已闭合：是**（`require_tests=true`）           |
| ~~Q3~~ | 启用阈值                  | **已闭合：** `len(tasks) > threshold`（默认 5）；行数由 **单批** `max_output_lines_per_batch` 控制，不单独触发 task_batch |
| Q4     | partial 标记            | `notes` vs `batches_completed` 字段         |
| Q5     | 签名提取首期                | 仅 Python Tier A vs 五语言启发式                 |
| Q6     | 前向引用扫描                | warn-only vs 硬拒收                          |


---

## 17. 废弃

- 图级 micro-QA
- LLM 决定 task 顺序
- 每批返回全 repo
- 重试时重新 task_batch
- §2 与 §3 决策编号混用（v2 已统一为 B0–B12）

---

## 18. 审查记录（v2）


| 维度       | 结论                                           |
| -------- | -------------------------------------------- |
| **合理性**  | 静态 Plan + 结构闭包 + 文件/行数双预算 + 一次 QA；与 retry 正交            |
| **架构**   | 节点内扩展，图路由不变；超大单 task 由 Architect 拆分，引擎 fail-fast               |
| **章节**   | v2.1 增补 §5.4 体积预算、§9.1.1 trim 表、§8.2 输出超集规则；门禁唯一权威在 §8 |
| **残余风险** | 无 micro-QA 导致缺陷晚发现；`depends_on` 遗漏无法由引擎推断    |


---

**一句话：** Architect 出 DAG → 引擎 **静态**生成有序 `batches` → 每批 **结构闭包**交付 → 整轮一次 QA；重试走 `retry_patch`。