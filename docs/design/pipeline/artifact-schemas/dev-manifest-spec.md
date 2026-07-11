# dev-manifest-spec.md — DevManifest（Developer JSON 契约）

## 依赖上游文档（只读）

审查 / 修订本文时 **仅以本表及正文字段定义为准**。`artifact-templates/dev-principles-spec` 为**下游**，不在此表列出。


| 分类            | 上游文档                                                                | 定位                                    |
| ------------- | ------------------------------------------------------------------- | ------------------------------------- |
| **总设计**       | [multi-agent-pipeline-design.md](../multi-agent-pipeline-design.md) | 系统的总体设计书 |
| **上游 JSON 契约** | [design-spec.md](./design-spec.md)                                  | 上游 JSON 契约 design-spec.md（`dev_tasks[]`、`file_plan[]`） |


---

> **实现：** `multi_agent_code_factory/schemas/dev_manifest.py`  
> **Run 路径：** `dev_manifest.json`  
> **产生方式：** Developer 节点（`role_id=developer`）；Live 为 Structured Output + Tool 写盘  
> **上游：** [design-spec.md](./design-spec.md) → `dev_tasks[]`、`file_plan[]`

## 原则

DevManifest 层 **语言无关**。源码与测试文件写入 Profile.`code_root`（仓库外生成项目）；本 JSON **只记录变更账本**（完成了哪些 `dev_tasks`、改了哪些路径），供 QA / Reviewer / 重试上下文使用。

| 分工 | 落点 |
|------|------|
| **代码正文** | `{code_root}/**`（Developer Tool：`write_file`） |
| **任务拓扑** | 上游 `design.json` → `dev_tasks[]`、`file_plan[]` |
| **本契约** | `dev_manifest.json` |

**校验：** 仅 Pydantic 结构校验；**无**独立 `dev_validate` 节点。实现质量由 QA（`run_tests`）与 Reviewer 把关。

**MVP 未 enforce 的契约意图（Reviewer / 人工可对照）：** `tasks_completed` 须对应 `design.dev_tasks[].id`；`changed_files[].path` 须相对 `code_root`、禁止 `..` 与绝对路径（design validate 对 design 路径有类似规则，manifest 本身不二次校验）。

## 产生流程（Live）

1. Developer 读取顶层 `prd`、`design`（`watch`）；实现环另注入瘦身后 `retry_bundle`（`failure_contexts` 等，见 [developer-retry-context-spec.md](../developer-retry-context-spec.md)）。  
2. LLM 返回 [`DeveloperLLMOutput`](../../../multi_agent_code_factory/agents/llm/schemas.py)（`tasks_completed`、`source_files[]`、`notes?`；**不含** `reflection` / `needs_architect` 等 DevManifest 扩展字段）。  
3. 引擎将 `source_files` 写入 `code_root`（重试时 `patch_only=True`，仅 merge 变更文件）。  
4. 若 Profile.`tools` 含 `linter`，执行 `toolchain.lint_command` → 填充 `lint_passed`（**`false` 不阻断**流水线，仍进入 QA）。  
5. 组装 `DevManifest` 并写入 `docs/runs/<task_id>/dev_manifest.json`。

**Stub：** 读取 fixture（如 `tests/fixtures/dev-manifest-todo.json`），不写 `code_root`。

## 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | `"1"` | |
| `tasks_completed` | string[] | 本轮完成的 `design.dev_tasks[].id` |
| `changed_files` | ChangedFile[] | 相对 `code_root` 的变更路径列表 |
| `lint_passed` | boolean? | Profile 启用 `linter` 且已跑 lint 时写入；未跑则为 `null`；**`false` 不阻断**图路由 |
| `needs_architect` | boolean | Developer 认为需改设计；默认 `false`；**路由以 Reviewer `next_stage` 为准** |
| `escalation_note` | string? | 给 Architect / Reviewer 的说明 |
| `reflection` | DevReflection? | Reflexion 结构化反思（实现环重试） |
| `incremental_plan` | string? | 增量 run 相对 `spec.parent_task_id` 的意图（P2） |
| `notes` | string? | 自由备注 |

### 字段写入方（当前实现）

| 字段 | Live 谁写 | 备注 |
|------|-----------|------|
| `tasks_completed` | LLM → 引擎 | 须为 design 中存在的 task id |
| `changed_files` | 引擎由 `source_files` 推导 | 当前 Live **一律** `change_type: create` |
| `lint_passed` | 引擎（可选） | 仅当 Profile 注册 `linter` |
| `notes` | LLM → 引擎 | |
| `needs_architect` | LLM（目标）/ 默认 false | 未接入 Developer 输出时恒为 false |
| `escalation_note` | LLM（目标） | 可选；未强制 |
| `reflection` | LLM（目标） | RetryBundle 已支持读取；Live 填充为 P1 |
| `incremental_plan` | LLM（目标） | 依赖 `--parent-task-id`（P2） |

### ChangedFile

| 字段 | 类型 | 说明 |
|------|------|------|
| `path` | string | 相对 `code_root`；POSIX 斜杠；禁止 `..` 与绝对路径 |
| `change_type` | enum | `create` \| `modify` \| `delete` |

**路径约定：**

- 与 `design.file_plan[].path` 布局一致（如 `src/`、`tests/`）。
- **Live 现状：** 每轮写入的 `source_files` 均记为 `create`（含覆盖写）；`modify` / `delete` 为 schema 预留，供增量 run 或显式删文件时使用。  
- **stale 策略：** **实现环**（`test_report.passed=false` / Reviewer `next_stage=developer`）重试 Developer 时，`dev_manifest.json` **不**标记 stale，State 保留上一轮 manifest。**升环**至 Architect/PM 时，`dev_manifest.json` 记入 `run_meta.stale_artifacts[]`；新一轮 Developer 应对照新版 `design` 重新申报 `changed_files`（`{code_root}` 源码不自动删除，见主线 §4.3）。

### DevReflection

| 字段 | 类型 | 说明 |
|------|------|------|
| `attempt` | integer | ≥ 1；通常对齐 `impl_retry_count + 1` |
| `hypothesis` | string | 失败原因假设 |
| `next_action` | string | 下一轮修复意图 |

## 与 design 追溯

| DevManifest | design.json |
|-------------|-------------|
| `tasks_completed[]` | `dev_tasks[].id`（如 `T1`） |
| `changed_files[].path` | `dev_tasks[].path`、`file_plan[].path` |

Reviewer 可对照 `tasks_completed` 是否覆盖 P0 `dev_tasks`；**当前 QA 节点不单独校验** task 覆盖率。缺测由 [`test_report.tests_missing`](./test-report-spec.md) 暴露；检测时优先用 `dev_manifest.changed_files`，若 manifest 缺失则回退 `design.file_plan`。

## 消费方

| 消费者 | 用途 |
|--------|------|
| **`qa`** | **非 LLM 节点**；将 State 中 `dev_manifest` 传入 `run_tests` → [`tests_missing`](./test-report-spec.md)；在 `code_root` 执行 Profile.`toolchain` |
| **`reviewer`** | prompt 注入 `dev_manifest`；对照 `tasks_completed` / `changed_files`；`git_diff` 以 `changed_files` 路径过滤（**非** DevManifest 字段，见 `prompt_context.py`） |
| **`deploy_hitl`** | watch 含 `dev_manifest`；人工审批前对照变更范围（与 `review` / `design` 同看） |
| **RetryBundle** | `impl_retry_count > 0` 时注入 Developer prompt（**不含**内嵌 `prd`/`design`）；含 `test_report`、`review_feedback?`、`dev_manifest`、`failure_contexts[]`、`reflection?`；详见 [developer-retry-context-spec.md](../developer-retry-context-spec.md) |
| **图路由** | **不读** DevManifest；实现环由 `test_report.passed` / Reviewer `next_stage` 决定 |

## 示例

### 样例 A — MVP 首次实现（与 stub fixture 一致）

```json
{
  "version": "1",
  "tasks_completed": ["T1"],
  "changed_files": [
    { "path": "src/todo_store.py", "change_type": "create" },
    { "path": "src/cli.py", "change_type": "create" }
  ],
  "lint_passed": true
}
```

### 样例 B — 实现环重试（含 reflection，P1 目标形态）

> Live 路径尚未强制产出 `reflection`；RetryBundle 与 schema 已就绪。

```json
{
  "version": "1",
  "tasks_completed": ["T1", "T2"],
  "changed_files": [
    { "path": "src/todo_store.py", "change_type": "create" },
    { "path": "tests/test_todo.py", "change_type": "create" }
  ],
  "lint_passed": true,
  "needs_architect": false,
  "reflection": {
    "attempt": 2,
    "hypothesis": "save 未 flush 导致测试失败",
    "next_action": "在 save 后显式 fsync"
  },
  "notes": "Fixed persistence flush on retry"
}
```
