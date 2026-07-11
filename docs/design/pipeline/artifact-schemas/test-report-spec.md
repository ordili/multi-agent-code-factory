# test-report-spec.md — TestReport（QA JSON 契约）

## 依赖上游文档（只读）

审查 / 修订本文时 **仅以本表及正文字段定义为准**；测试命令见 [profiles.md](../profiles.md)。


| 分类            | 上游文档                                                         | 定位                                       |
| ------------- | ------------------------------------------------------------ | ---------------------------------------- |
| **总设计**       | [multi-agent-pipeline-design.md](../multi-agent-pipeline-design.md) | 系统的总体设计书 |
| **上游 JSON 契约** | [design-spec.md](./design-spec.md)                            | 上游 JSON 契约 design-spec.md（`test_cases` 字段语义） |
| **运行配置**      | [profiles.md](../profiles.md)                                | `toolchain` 测试命令与解析器                      |


---

> **实现：** `multi_agent_code_factory/schemas/test_report.py`  
> **Run 路径：** `test_report.json`  
> **产生方式：** `run_tests` Tool（**非 LLM 编造**）

## 原则

Test 层 **语言无关**。pytest、`cargo test`、`go test`、`mvn test`、`forge test` 等均为 Profile.[`toolchain`](../profiles.md)；流水线只消费统一 `TestReport`。

## 执行流程

1. （可选）`toolchain.setup` / `build`  
2. 对照 Profile.`tests_missing` 与 `test_dir_glob` 检测 `tests_missing`（范围、detector 见 [qa-gates-spec.md §3](../qa-gates-spec.md)）  
3. 执行 `test_command`（`cwd=code_root`）  
4. `test_parser` 解析 → 基础结果  
5. （可选）执行 Profile.`coverage` 命令并解析 → `coverage` 块（见 [qa-gates-spec.md §4](../qa-gates-spec.md)）  
6. 按 [qa-gates-spec.md §2](../qa-gates-spec.md) 合并 `passed`  
7. `passed=false` → 实现环回 Developer（仅当 Layer 1 失败或 Profile.`block_on` 触发）

> **历史行为：** 曾以「`tests_missing` 非空即 `passed=false`」为唯一规则；Rust 等语言见 qa-gates-spec 修订。

## 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | `"1"` | |
| `passed` | boolean | 见 [qa-gates-spec.md §2](../qa-gates-spec.md)（工具链 + 可选 block_on） |
| `exit_code` | integer | 进程退出码 |
| `summary` | object | `{ total, passed, failed, skipped }` |
| `failures` | TestFailure[] | 失败用例 |
| `duration_sec` | number | 耗时 |
| `command` | string | 实际 `test_command` |
| `parser` | string | `test_parser` id |
| `language` | string? | Profile.`language` 快照 |
| `tests_missing` | string[]? | 缺测的模块/路径（启发式；是否 block 见 Profile） |
| `coverage` | CoverageReport? | 代码覆盖率（可选；见 §CoverageReport） |
| `acceptance_traceability` | AcceptanceTraceItem[]? | AC 追溯（P4；见 [qa-gates-spec §8](../qa-gates-spec.md)） |
| `raw_output_tail` | string? | 兜底调试输出 |

### AcceptanceTraceItem

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | PRD acceptance_criteria id |
| `designed` | boolean | `test_cases.covers` 是否含该 AC |
| `test_case_ids` | string[] | 关联 TC id |
| `met` | boolean | designed 且工具链绿 |
| `note` | string? | 缺口说明 |

### CoverageReport

可选。Profile.`coverage.enabled=true` 时由 `run_tests` 写入。完整语义见 [qa-gates-spec.md §4](../qa-gates-spec.md)。

| 字段 | 类型 | 说明 |
|------|------|------|
| `tool` | string | 工具标识（如 `pytest-cov`、`llvm-cov`） |
| `command` | string | 实际 coverage 命令 |
| `parser` | string | `coverage_parser` id |
| `line_percent` | number? | 行覆盖率 0–100 |
| `branch_percent` | number? | 分支覆盖率 0–100 |
| `lines_covered` | integer? | 可选 |
| `lines_total` | integer? | 可选 |
| `thresholds` | object? | `{ line_percent?, branch_percent? }` 快照 |
| `passed` | boolean | 相对 thresholds 是否达标 |
| `violations` | string[]? | 未达标说明 |
| `raw_summary_path` | string? | 原始报告相对 `code_root` |

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
