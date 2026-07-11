# QA 门禁规格 — tests_missing、coverage 与 TestReport.passed

## 依赖上游文档（只读）

| 分类 | 上游文档 | 定位 |
|------|----------|------|
| **总设计** | [multi-agent-pipeline-design.md](../multi-agent-pipeline-design.md) | 流水线回路、impl_retry |
| **TestReport 字段** | [test-report-spec.md](./artifact-schemas/test-report-spec.md) | JSON 契约 |
| **Profile 载体** | [profiles.md](./profiles.md) | YAML 配置 |
| **Design 追溯** | [design-spec.md](./artifact-schemas/design-spec.md) | `test_cases`、`dev_tasks` |

---

> **状态：** 设计定稿（PR1/PR2/PR3 已实现；P4 待定）  
> **动机：** Rust live run 出现 `cargo test` 通过仍因 `tests_missing` 耗尽 `impl_retry`（文件 stem 启发式 vs `#[cfg(test)]` / 集成测命名）。  
> **原则：** 工具链测试 = **硬门禁**；缺测启发式 / 代码覆盖率 = **可配置辅助信号**。

## 1. 三层 QA 模型

```text
Layer 1  工具链测试（必须）
         test_command + test_parser → summary.failed == 0, exit_code == 0
         失败 → passed=false → impl 环

Layer 2  缺测检测 tests_missing（可选，Profile 配置）
         语言感知 detector；默认 Rust warn、Python block
         见 §3

Layer 3  代码覆盖率 coverage（可选，Profile 配置）
         coverage_command + coverage_parser → line/branch 阈值
         默认关闭；开启时建议 warn 或 Reviewer finding，见 §4
```

**与 Design 的关系（并行，非替代）：**

- `design.test_cases[].covers` → 需求/AC **是否被设计到**（design_validate / semantic）
- Layer 3 → 实现代码 **是否被执行到**
- 二者互补，不互相替代

---

## 2. TestReport.passed 判定（规范）

实现：`run_tests` 在 parser 结果上合并 Layer 2/3 后写入 `passed`。

```text
toolchain_ok =
    exit_code == 0
    AND summary.failed == 0

if NOT toolchain_ok:
    passed = false

elif tests_missing 非空 AND profile.tests_missing.block_on == true:
    passed = false

elif coverage 存在 AND coverage.passed == false AND profile.coverage.block_on == true:
    passed = false

else:
    passed = true
```

**说明：**

- `tests_missing` **始终写入** `test_report.json`（可为 `[]` 或省略），即使 `block_on=false`
- `coverage` 未启用时字段为 `null` / 省略
- QA 日志：工具链通过但 Layer 2/3 有告警时打 `WARNING`，文案使用 `toolchain green`（禁止硬编码 pytest）

---

## 3. Profile：`tests_missing`

### 3.1 YAML 结构

```yaml
tests_missing:
  enabled: true              # false 时跳过检测
  block_on: false            # true → 非空则 passed=false
  detector: rust             # file_stem | rust | go | solidity（见 §3.3）
  inline_tests: true           # rust：扫描 #[cfg(test)] / #[test]
  scope: dev_tasks             # dev_tasks | manifest（见 §3.4）
  retry_hint: |                # 注入 Developer 重试 extra_system
    For each listed path, add tests/<module>.rs or #[cfg(test)] in the source file.
```

**`_base/common.yaml` 建议默认：**

```yaml
tests_missing:
  enabled: true
  block_on: true
  detector: file_stem
  inline_tests: false
  scope: dev_tasks
```

**`profiles/rust.yaml` 覆盖：**

```yaml
tests_missing:
  block_on: false
  detector: rust
  inline_tests: true
  retry_hint: |
    For each listed path, add tests/<stem>.rs under tests/ or unit tests via #[cfg(test)] in the same module.
```

**`profiles/python.yaml`：** 继承 common（`block_on: true`, `detector: file_stem`），`retry_hint` 指向 `tests/test_<module>.py`。

### 3.2 Pydantic（实现目标）

```python
class TestsMissingConfig(BaseModel):
    enabled: bool = True
    block_on: bool = True
    detector: str = "file_stem"  # file_stem | rust | go | solidity
    inline_tests: bool = False
    scope: str = "dev_tasks"     # dev_tasks | manifest
    retry_hint: str | None = None
```

挂载于 `ProfileConfig.tests_missing: TestsMissingConfig`。

### 3.3 Detector 语义

#### `file_stem`（Python、Java MVP）

- 源码路径来自 §3.4 范围
- 测试文件：`test_dir_glob` 命中路径
- 匹配：`test_<stem>.py`、`<stem>_test.py`、Java `*Test.java` 等（与现 `tests_missing.py` 一致）
- 豁免：`__init__.py`、`main` 等等价

#### `rust`

在 `file_stem` 规则之外，**任一满足即视为已覆盖：**

1. stem 匹配独立测试文件（`tests/calc.rs`、`tests/calc_test.rs`）
2. `inline_tests=true` 时，读取源码文本含 `#[cfg(test)]` 或 `#[test]`
3. 路径 basename 为 `main.rs`、`lib.rs`、`mod.rs` → 豁免

**不要求** `tests/integration_test.rs` 与 `src/calc.rs` stem 对应。

#### `go`（P2）

- 同目录或同 package 下 `*_test.go` 覆盖对应 `.go` 源文件（非 `_test.go` 本身）

#### `solidity`（P2）

- `test/<Contract>.t.sol` 或 `test/**` 与 `src/<Contract>.sol` 映射；Foundry 测试绿 + detector warn

### 3.4 检测范围 `scope`

| `scope` | 源码路径来源 |
|---------|----------------|
| `dev_tasks`（**推荐**） | `design.dev_tasks[].path`；有 manifest 时取与 `changed_files` 交集 |
| `manifest` | 现行为：`dev_manifest.changed_files` 非测试路径 |

避免对 `Cargo.toml`、`README.md` 等误报。

### 3.5 Developer 重试

`format_qa_retry_feedback` **必须**使用 `profile.tests_missing.retry_hint`，禁止写死 Python 路径。

当 `block_on=false` 时，`auto_generate_tests` **不触发** impl 环；`tests_missing` 仍写入 `test_report` 并注入 Reviewer / `prompt_context`（warn finding）。

---

## 4. Profile：`coverage`（Layer 3，可选）

### 4.1 YAML 结构

```yaml
coverage:
  enabled: false
  block_on: false              # true 时 coverage.passed=false → TestReport.passed=false
  command: python -m pytest -q --cov=. --cov-report=json:coverage.json
  parser: pytest_cov_json      # 插件 id
  artifacts:                   # parser 读取路径（相对 code_root）
    - coverage.json
  thresholds:
    line_percent: 70           # null 表示只记录不判阈值
    branch_percent: null
  include_globs:               # 可选；统计范围
    - "src/**"
  exclude_globs:
    - "tests/**"
```

**分语言推荐（启用时）：**

| Profile | `command`（示例） | `parser` | 备注 |
|---------|-------------------|----------|------|
| `python` | `pytest --cov=src --cov-report=json:coverage.json` | `pytest_cov_json` | 本地/CI 优先试点 |
| `go` | `go test -coverprofile=coverage.out ./...` | `go_cover` | 内置，成本低 |
| `rust` | `cargo llvm-cov report --summary-only --json` | `llvm_cov_json` | **建议仅 Linux CI**；本地 Windows 可 `enabled: false` |
| `java` | `mvn -q test jacoco:report` | `jacoco_xml` | P3 |
| `solidity` | `forge coverage --report summary` | `forge_coverage` | P3 |

### 4.2 Pydantic（实现目标）

```python
class CoverageThresholds(BaseModel):
    line_percent: float | None = Field(default=None, ge=0, le=100)
    branch_percent: float | None = Field(default=None, ge=0, le=100)


class CoverageConfig(BaseModel):
    enabled: bool = False
    block_on: bool = False
    command: str | None = None
    parser: str = "exit_code_only"
    artifacts: list[str] = Field(default_factory=list)
    thresholds: CoverageThresholds = Field(default_factory=CoverageThresholds)
    include_globs: list[str] = Field(default_factory=list)
    exclude_globs: list[str] = Field(default_factory=list)
```

### 4.3 TestReport.`coverage` 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `coverage` | CoverageReport? | 未启用时为 `null` |

#### CoverageReport

| 字段 | 类型 | 说明 |
|------|------|------|
| `tool` | string | 如 `pytest-cov`、`llvm-cov`、`go-cover` |
| `command` | string | 实际执行的 coverage 命令 |
| `parser` | string | `coverage_parser` id |
| `line_percent` | number? | 0–100，无法解析时为 `null` |
| `branch_percent` | number? | 0–100 |
| `lines_covered` | integer? | 可选明细 |
| `lines_total` | integer? | 可选明细 |
| `thresholds` | object? | 快照 Profile 阈值 `{ line_percent, branch_percent }` |
| `passed` | boolean | 相对 thresholds 是否达标；无阈值时为 `true` |
| `violations` | string[]? | 人类可读，如 `line 62.3% < threshold 70%` |
| `raw_summary_path` | string? | 相对 `code_root` 的原始报告路径 |

**`coverage.passed` 计算：**

```text
若 line_percent 阈值非 null 且 line_percent < 阈值 → violations += ...; passed=false
若 branch_percent 阈值非 null 且 branch_percent < 阈值 → 同理
若无任何阈值配置 → passed=true（仅记录 metrics）
```

### 4.4 示例（Python，启用 coverage）

```json
{
  "version": "1",
  "passed": true,
  "exit_code": 0,
  "summary": { "total": 5, "passed": 5, "failed": 0, "skipped": 0 },
  "failures": [],
  "command": "python -m pytest -q --junitxml=reports/junit.xml",
  "parser": "junit_xml",
  "language": "python",
  "tests_missing": [],
  "coverage": {
    "tool": "pytest-cov",
    "command": "python -m pytest -q --cov=src --cov-report=json:coverage.json",
    "parser": "pytest_cov_json",
    "line_percent": 84.2,
    "branch_percent": null,
    "lines_covered": 421,
    "lines_total": 500,
    "thresholds": { "line_percent": 70, "branch_percent": null },
    "passed": true,
    "violations": [],
    "raw_summary_path": "coverage.json"
  }
}
```

### 4.5 Reviewer 与 coverage

当 `coverage.enabled` 且 `block_on=false`：

- `prompt_context` 注入 `test_report.coverage` 摘要
- Reviewer 对 `coverage.passed=false` 或 `tests_missing` 非空添加 `findings[]`（severity `warn`），**不强制** `next_stage=developer`（除非 AC 未满足）

---

## 5. 执行顺序（run_tests）

```text
1. detect_tests_missing(scope, detector)     → tests_missing[]
2. （可选）setup / build
3. 执行 test_command → parser → base TestReport
4. （若 coverage.enabled）执行 coverage.command → coverage_parser → coverage 块
5. 按 §2 合并 passed
6. 写入 test_report.json
```

Coverage **不替代** test_command；先测后覆盖率（或 Profile 文档约定合并命令，但解析仍分 parser）。

---

## 6. 实施分期

| 阶段 | 内容 | 验收 |
|------|------|------|
| **PR1** | `tests_missing` Profile 配置；§2 passed 公式；Rust `block_on: false`；`retry_hint`；QA 日志 | calculator-rust-2 类 run `status=completed` |
| **PR2** | `rust` detector（inline + dev_tasks scope + 豁免）；单测 fixture | `src/calc.rs` + `#[cfg(test)]` 不再出现在 tests_missing |
| **PR3a** | Python `coverage` + `pytest_cov_json` parser + schema | test_report 含 coverage 块 |
| **PR3b** | Go `go_cover`；Rust `llvm_cov_json`（CI only） | 可选阈值 warn |
| **P4** | Design `test_cases` → AC 追溯 + jacoco/forge coverage parsers | ✅ 已实现 |

---

## 8. P4：`acceptance_traceability`（AC 追溯）

### 8.1 语义

在 QA 阶段，将 PRD `acceptance_criteria[]` 与 Design `test_cases[].covers` 及工具链结果对齐：

| 字段 | 说明 |
|------|------|
| `id` | AC id（如 `AC-1`） |
| `designed` | 是否存在 `test_cases.covers` 含该 AC |
| `test_case_ids` | 覆盖该 AC 的 TC id 列表 |
| `met` | `designed` 且工具链绿（`exit_code=0` 且 `summary.failed=0`） |
| `note` | 未设计 / 工具链失败说明 |

**与 Design 校验分工：**

- `DES-101` / `DES-016`（design_validate）：设计阶段 AC 是否被 trace / test_cases 覆盖
- P4（QA）：实现后工具链是否绿，并预填 `test_report.acceptance_traceability` 供 Reviewer 写 `acceptance_coverage`

### 8.2 Profile

```yaml
acceptance_traceability:
  enabled: true
  block_on: false   # true 时 designed 但未 met 的 AC 可令 passed=false
```

默认继承 `_base/common.yaml`（`block_on: false`，仅 inform Reviewer）。

### 8.3 执行

`run_tests(..., prd=, design=)` 在 finalize 前调用 `compute_acceptance_traceability`；Reviewer prompt 注入 `acceptance_traceability` 作为 `acceptance_coverage` 基线。

### 8.4 Coverage parsers（Java / Solidity）

| Profile | `parser` | 输入 |
|---------|----------|------|
| `java` | `jacoco_xml` | `target/site/jacoco/jacoco.xml` |
| `solidity` | `forge_coverage` | `forge coverage --report summary` stdout |

---

## 9. 相关文件（P4）

| 用途 | 路径 |
|------|------|
| Schema | `schemas/test_report.py`、`profile_config/models.py` |
| 检测 | `tools/tests_missing.py`、`tools/ac_traceability.py` |
| 运行 | `tools/run_tests.py`、`tools/run_coverage.py` |
| Coverage | `tools/coverage_parsers/`（含 `jacoco_xml`、`forge_coverage`） |
| 重试文案 | `agents/llm/prompt/validation_feedback.py` |
| Profile | `profiles/_base/common.yaml`、`profiles/rust.yaml`、`profiles/python.yaml` |
| 测试 | `tests/test_tests_missing.py`、`tests/test_coverage_parsers.py` |

---

*最后更新：2026-07-11（calculator-rust-2 tests_missing 根因；三层 QA + coverage 字段定稿）*
