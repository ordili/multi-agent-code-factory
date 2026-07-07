# DevManifest — Developer 输出

> **实现：** `multi_agent_code_factory/schemas/dev_manifest.py`  
> **Run 路径：** `dev_manifest.json`  
> **生产者：** `role_id=developer`

代码通过 Tool 写入 Profile.`code_root`；JSON 只记录 **变更清单**，供 QA / Reviewer 使用。

## 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | `"1"` | |
| `tasks_completed` | string[] | 完成的 `dev_tasks.id` |
| `changed_files` | ChangedFile[] | 变更文件列表 |
| `lint_passed` | boolean? | 若跑过 linter |
| `needs_architect` | boolean | Developer 认为需改设计（默认 false；路由以 Reviewer 为准） |
| `escalation_note` | string? | 给 Architect / Reviewer |
| `reflection` | object? | Reflexion：`{ "attempt", "hypothesis", "next_action" }` |
| `incremental_plan` | string? | 增量 run 相对 parent 的意图 |
| `notes` | string? | |

### ChangedFile

`{ "path", "change_type": "create"|"modify"|"delete" }`

## 消费方

| 消费者（role_id） | 用途 |
|-------------------|------|
| **`qa`** | 对照 `design.dev_tasks` 与变更范围 |
| **`reviewer`** | diff、验收覆盖 |
| **RetryBundle** | `changed_files` + `test_report.failures[].file` 读代码片段 |

## 示例

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
  }
}
```
