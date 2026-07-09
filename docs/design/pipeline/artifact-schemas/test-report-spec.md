# test-report-spec.md — TestReport（QA JSON 契约）

> **实现：** `multi_agent_code_factory/schemas/test_report.py`  
> **Run 路径：** `test_report.json`  
> **产生方式：** `run_tests` Tool（**非 LLM 编造**）

## 原则

Test 层 **语言无关**。pytest、`cargo test`、`go test`、`mvn test`、`forge test` 等均为 Profile.[`toolchain`](../profiles.md)；流水线只消费统一 `TestReport`。

## 执行流程

1. （可选）`toolchain.setup` / `build`  
2. 对照 `test_dir_glob` 检测 `tests_missing`：优先 `dev_manifest.changed_files`，无 manifest 时回退 `design.file_plan`  
3. 执行 `test_command`（`cwd=code_root`）  
4. `test_parser` 解析 → `TestReport`  
5. `passed=false` → 实现环回 Developer

## 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | `"1"` | |
| `passed` | boolean | 全部通过 |
| `exit_code` | integer | 进程退出码 |
| `summary` | object | `{ total, passed, failed, skipped }` |
| `failures` | TestFailure[] | 失败用例 |
| `duration_sec` | number | 耗时 |
| `command` | string | 实际 `test_command` |
| `parser` | string | `test_parser` id |
| `language` | string? | Profile.`language` 快照 |
| `tests_missing` | string[]? | 缺测试的模块/路径 |
| `raw_output_tail` | string? | 兜底调试输出 |

### TestFailure

| 字段 | 类型 | 说明 |
|------|------|------|
| `test_id` | string | 框架内唯一 id |
| `suite` | string? | 套件 / 类 / package |
| `name` | string? | 用例短名 |
| `file` | string? | 相对 `code_root` |
| `line` | integer? | 失败行 |
| `message` | string | 摘要 |
| `output` | string? | 截断 stack trace |

**`exit_code_only` 兜底：** `passed = (exit_code == 0)`，`failures` 至多一条含 stderr 尾部。

## 示例

```json
{
  "version": "1",
  "passed": false,
  "exit_code": 1,
  "summary": { "total": 12, "passed": 11, "failed": 1, "skipped": 0 },
  "failures": [
    {
      "test_id": "tests.test_todo.TestAdd::test_add",
      "file": "tests/test_todo.py",
      "line": 14,
      "message": "AssertionError: expected 2 items"
    }
  ],
  "duration_sec": 1.23,
  "command": "pytest -q --junitxml=reports/junit.xml",
  "parser": "junit_xml",
  "language": "python"
}
```
