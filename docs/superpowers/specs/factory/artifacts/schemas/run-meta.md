# RunMeta — run 元数据

> **实现：** `multi_agent_code_factory/schemas/run_meta.py`  
> **Run 路径：** `docs/factory/runs/<task_id>/run_meta.json`

每次 `python -m multi_agent_code_factory run` 写入；用于运维、resume、预算与回路审计。

## 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | `"1"` | |
| `task_id` | string | 任务 id |
| `profile` | object | Profile 快照（含 `id`、`language`、`toolchain`） |
| `loop_limits` | object | 本次 run 生效的上限 |
| `impl_retry_count` | integer | 实现环计数 |
| `design_revision_count` | integer | 设计环计数 |
| `spec_revision_count` | integer | 需求环计数 |
| `budget` | object? | `{ max_llm_calls, max_tokens, used_* }` |
| `checkpoint_id` | string? | LangGraph checkpoint（P1） |
| `deploy_status` | string | `skipped` \| `success` \| `failed` |
| `status` | string? | `running` \| `failed` \| `completed`（`on_limit_exceeded=fail` 触顶时为 `failed`） |
| `hitl_history` | object[]? | 历次 HITL 决议摘要（P1）；当前待决见 `hitl.json` |
| `stale_artifacts` | string[]? | 升环后 supersede 的文件路径（P1） |
| `artifact_layout` | string? | 多轮 design 布局约定 |
| `started_at` / `finished_at` | string? | ISO8601 |

## 示例

```json
{
  "version": "1",
  "task_id": "todo-cli",
  "profile": {
    "id": "default",
    "language": "python",
    "code_root": "D:/code/generated/default"
  },
  "loop_limits": {
    "max_impl_retries": 3,
    "max_design_revisions": 2,
    "max_spec_revisions": 1
  },
  "impl_retry_count": 1,
  "design_revision_count": 0,
  "spec_revision_count": 0,
  "deploy_status": "skipped"
}
```

配置优先级：CLI → `FACTORY_*` env → `config/autonomy_policy.yaml` → 默认（见主线 §4.4）。
