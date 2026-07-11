# Developer 重试上下文优化 — 设计规格（已实现）

> **日期：** 2026-07-11  
> **状态：** 已实现  
> **实现落点：** `prompt_context.py` · `retry_context.py` · `tools/traceback/*` · `tools/snippet_extract.py` · `developer_output.py` · `agents/developer.py`  
> **触发条件：** 实现环重试（`impl_retry_count > 0`）—— QA `test_report.passed=false` 或 Reviewer `next_stage=developer` 后再次进入 Developer 节点。  
> **关联：** [multi-agent-pipeline-design.md §4.5.1](./multi-agent-pipeline-design.md#451-developer-重试retrybundleexecutable-feedback) · [test-report-spec.md](./artifact-schemas/test-report-spec.md) · [dev-manifest-spec.md](./artifact-schemas/dev-manifest-spec.md)

---

## 1. 我们要解决什么

实现环重试时，Developer 的 **输入** 与 **输出** 策略共同决定：能否修好、Token 花多少、是否误改已通过代码。当前实现有三类缺陷：

### 1.1 Token 消耗过高


| 现象                   | 原因                                                     |
| -------------------- | ------------------------------------------------------ |
| 重试 **prompt** 偏大     | `retry_bundle` 内重复携带 `prd` + `design`（顶层 `watch` 已有一份） |
| 重试 **completion** 最大 | 每轮仍要求 LLM 返回**全部** `source_files` 完整内容，即使只改 1–2 个文件    |


**目标：** 在不影响修 bug 的前提下，降低重试轮次的 input / output Token（预期 completion 可降 60%–90%）。

### 1.2 输入不正确、不完备


| 现象              | 原因                                           |
| --------------- | -------------------------------------------- |
| 看不到根因所在**业务函数** | 只读 `failures[].file`，且多为测试文件路径               |
| 看不到**调用链**      | 未解析 `failure.output`（traceback）；未按「谁调谁」组织上下文 |
| 截断不可知           | 缺少 `omitted_*` 字段，LLM 不知道哪些帧/文件未注入           |


**目标：** 重试输入能支撑「定位根因 → 理解调用关系 → 最小修复」，而非凭 `design` 猜测未注入的代码。

### 1.3 输出易回归


| 现象      | 原因                               |
| ------- | -------------------------------- |
| 修 A 坏 B | 输入只有局部片段，输出却要求全量文件；模型重写未注入的已通过文件 |


**目标：** 重试输出与输入对称——**只提交需要变更的文件**（patch），引擎 merge 写盘。

### 1.4 非目标

- 按 `dev_tasks` 多轮 Developer LLM（分片生成）
- LLM 主动 `read_file` Tool 拉取代码库
- 首期五语言均达到与 Python 相同的 **AST 级**函数定界精度（见 §6.4 分级）

---

## 2. 方案总览（问题 → 举措）


| 问题                | 举措                                                         | 决策    |
| ----------------- | ---------------------------------------------------------- | ----- |
| 1.1 input 重复      | **Bundle 瘦身**：`retry_bundle` 不含 `prd`/`design`             | D6    |
| 1.1 output 全量     | **Patch 模式**：`impl_mode=retry_patch`，仅返回变更文件               | D7    |
| 1.2 上下文不对         | **Call-Path Context**：traceback → 调用链 → **函数体** snippet    | D1–D5 |
| 1.2 traceback 不可用 | **失败闭包**兜底（test↔src 配对、tests_missing、review finding）       | D2 兜底 |
| 1.2 不可观测          | `omitted_frames` / `code_snippets_omitted_paths` 写入 bundle；**WARN 日志**（§9）待补 | §9    |
| 1.3 输出回归          | 与 D7 合并：`apply_developer_output(patch_only=True)`          | §8    |


```text
                    ┌─ D6: 顶层 prd/design 一份
  输入 Token 优化 ───┼─ D1–D5: failure_contexts（调用路径 × 函数体 × 预算）
                    └─ test_report 摘要（failures 列表、tests_missing）

  输出 Token 优化 ───── D7: retry_patch（仅 source_files 变更集）
```

---

## 3. 定稿决策


| #   | 决策        | 结论                                                      |
| --- | --------- | ------------------------------------------------------- |
| D1  | 上下文单元     | **函数体优先**（≤200 行整段）；超长函数 **前 100 + 后 20**；无法定界 **前 80 + 后 20** |
| D2  | 路径来源      | **主：** 解析 `failure.output` → `call_path[]`；**兜底：** 失败闭包 |
| D3  | 预算填充顺序    | **root_cause → caller → test**（先保证栈底用户代码）               |
| D4  | 框架帧       | 过滤 stdlib / site-packages / `target/` / `node_modules`  |
| D5  | 行数预算      | 全局上限（非固定每文件）：2000 行 / 12 函数 / 8 文件                      |
| D6  | Bundle 瘦身 | `retry_bundle` **不含** `prd`/`design`                    |
| D7  | Patch 输出  | 重试时 `impl_mode=retry_patch`                             |
| D8  | 首期语言范围  | **Python、Rust、Go、Java、Solidity** 五 Profile 均须可用（能力分级见 §6.4） |


---

## 4. 数据流

```text
test_report.failures[]
        │
        ▼
  TracebackParser (language) ──成功──► call_path[]: StackFrame
        │                                      │
        │ 失败                                  ▼
        ▼                              extract_function_body()
  失败闭包 (paired_paths 等)                    │
        │                                      ▼
        └──────────────► failure_contexts[] ──► retry_bundle
                                                    │
顶层 context: prd, design, profile（各一份）          │
                    impl_mode: retry_patch ◄────────┘
```

---

## 5. Schema

### 5.1 StackFrame

```python
class StackFrameRole(StrEnum):
    ROOT_CAUSE = "root_cause"   # 栈底用户代码（order 最小，最先占预算）
    CALLER = "caller"
    TEST = "test"

class StackFrame(BaseModel):
    order: int                  # 0 = root_cause，递增至 test
    role: StackFrameRole
    file: str                   # 相对 code_root
    line: int                   # 1-based
    function: str | None = None
```

**顺序约定（五语言统一）：** 自栈底（root_cause，`order=0`）向栈顶（test）递增；各语言 parser 负责将原生栈格式映射为该顺序。

### 5.2 FailureContext（每个失败用例一条）

```python
class FunctionSnippet(BaseModel):
    path: str
    function: str | None
    frame_order: int
    line_start: int
    line_end: int
    total_file_lines: int | None = None
    truncated: bool = False
    content: str

class OmittedFrame(BaseModel):
    file: str
    function: str | None = None
    line: int | None = None
    reason: Literal[
        "budget_exhausted", "framework_filtered",
        "read_failed", "no_function_bound",
    ]

class FailureContext(BaseModel):
    test_id: str
    message: str
    traceback_parse_ok: bool
    call_path: list[StackFrame]
    snippets: list[FunctionSnippet]
    omitted_frames: list[OmittedFrame] = []
```

### 5.3 RetryBundle（瘦身后）

```python
class ReviewFeedback(BaseModel):
    approved: bool
    summary: str
    findings: list[Finding]  # 仅 developer_fix / blocking

class RetryBundle(BaseModel):
    retry_cause: Literal["qa_failure", "review_rejection", "both"]
    test_report: TestReport | None = None   # 摘要层：summary、tests_missing、failures 元数据
    review_feedback: ReviewFeedback | None = None
    dev_manifest: DevManifest
    reflection: dict[str, Any] | None = None
    failure_contexts: list[FailureContext] = []
    code_snippets_omitted_paths: list[str] = []  # 预算触顶未处理的文件路径
```

**明确不含：** `prd`、`design`（顶层 `watch` 注入一次）。

**说明：** `test_report` 与 `failure_contexts` 分工不同——前者保留门禁字段（`tests_missing`、`summary`）；后者承载**调用路径 + 函数体正文**。不重复注入 prd/design。

**`retry_cause` 推断：**

```python
qa_failed = test_report is not None and not test_report.passed
review_failed = review is not None and not review.approved
# qa_failed and review_failed → "both"
# elif qa_failed → "qa_failure"
# elif review_failed → "review_rejection"
```

---

## 6. Call-Path 与函数体提取

### 6.1 栈帧解析（主路径）

**通用数据源（按 Parser 优先级）：**

| 字段 | 用途 |
|------|------|
| `TestFailure.output` | traceback / panic / stack 正文（**首选**） |
| `TestFailure.message` | 摘要；Solidity 等缺 output 时的补充 |
| `test_report.raw_output_tail` | parser 无结构化栈时的兜底文本 |

**模块布局：** `tools/traceback/<language>.py`，由 `tools/traceback/parse.py` 按 `profile.language` 分发。

### 6.2 函数体提取

**模块：** `tools/snippet_extract.py`，按 `profile.language` 分发定界策略。

| 情况         | 行为                                              |
| ---------- | ----------------------------------------------- |
| 函数 ≤ 200 行 | 完整函数体 |
| 函数 > 200 行 | **前 100 行 + 后 20 行**（`[max(1,line-100), min(total,line+20)]`），`truncated=true` |
| 无法定界       | **前 80 行 + 后 20 行**（`[max(1,line-80), min(total,line+20)]`），`truncated=true` |
| 读盘失败       | `omitted_frames`，`reason=read_failed`           |

**非对称 hunk（长函数与 fallback 共用原则）：** 出错行多为症状；根因逻辑多在**上方**，故向前多取、向后少取。

| 场景 | 向前 | 向后 |
|------|------|------|
| 函数 > 200 行 | 100 | 20 |
| 无法定界 | 80 | 20 |

### 6.3 预算常量与分配


| 常量                           | 值    |
| ---------------------------- | ---- |
| `SNIPPET_MAX_TOTAL_LINES`    | 2000 |
| `SNIPPET_MAX_FUNCTIONS`      | 12   |
| `SNIPPET_MAX_FILES`          | 8    |
| `SNIPPET_MAX_FUNCTION_LINES` | 200  | 超过则不再取整函数，改用长函数 hunk |
| `SNIPPET_LONG_FUNCTION_LINES_BEFORE` | 100  |
| `SNIPPET_LONG_FUNCTION_LINES_AFTER` | 20   |
| `SNIPPET_FALLBACK_LINES_BEFORE` | 80   |
| `SNIPPET_FALLBACK_LINES_AFTER` | 20   |


```text
for each failure:
  for frame in call_path ordered by frame.order ascending:
    if 全局 lines/functions/files 触顶 → omitted_frames; continue
    extract body → snippets; 更新全局计数
```

### 6.4 首期五语言能力矩阵（D8）

V1 内置 Profile 均须在本方案下可重试；**不要求**五语言能力完全一致，但均须达到「有结构化栈则用栈，否则闭包 + 非对称 hunk」。

| 语言 | Profile | `test_parser` | 栈帧来源 | 函数定界 | 首期 Tier |
|------|---------|---------------|----------|----------|-----------|
| **Python** | `python` | `junit_xml` | `failure.output`（pytest traceback） | `ast` | **A** |
| **Java** | `java` | `junit_xml` | `failure.output`（JUnit / Surefire stack） | 大括号启发式 → 失败则 hunk | **B** |
| **Rust** | `rust` | `cargo_json` | `failure.output`（panic / test stdout） | `fn` 块启发式 → 失败则 hunk | **B** |
| **Go** | `go` | `go_json` | `failure.output`（`go test -json` 失败输出） | `func` 启发式 → 失败则 hunk | **B** |
| **Solidity** | `solidity` | `forge_json` | `message` + `raw_output_tail` / stderr；无栈时用 `failure.file`+`line` | `function` 启发式 → 失败则 hunk | **C** |

**Tier 含义：**

| Tier | call-path | 函数体 |
|------|-----------|--------|
| **A** | 多帧 traceback，过滤框架路径 | AST 精确 |
| **B** | 从 output 解析 ≥1 用户帧（可能仅 1–2 帧） | 启发式定界为主 |
| **C** | 常无完整栈；优先 `failure.file`+`line` + 失败闭包 | 几乎总是非对称 hunk |

**首期前置依赖：**

| 项 | 状态 | 说明 |
|----|------|------|
| `cargo_json` | 已实现 | R1a 已增强：`failure.output` / `file` / `line` |
| `forge_json` | 已实现 | R1a 已增强：`failure.output` / `file` / `line` |
| `junit_xml` | 已有 | Python / Java 共用 |
| **`go_json`** | **已实现** | `tools/test_parsers/go_json.py` 已注册 |

**统一过滤规则（五语言共用）：** 去掉标准库、依赖缓存、`target/`、`node_modules`、`vendor/`、`.venv` 等非 `code_root` 业务路径。

**Python traceback 示例（Tier A）：**

```text
Traceback (most recent call last):
  File "tests/test_calc.py", line 14, in test_mixed
  File "src/calc_core.py", line 45, in evaluate
  File "src/calc_core.py", line 102, in _parse
ValueError: ...
```

→ `order=0` 为栈底用户帧（root_cause），递增向 test。

### 6.5 失败闭包（兜底）

当 `traceback_parse_ok=false`：


| 级别  | 来源                                                                  |
| --- | ------------------------------------------------------------------- |
| F0  | `failure.file` + `failure.line`                                     |
| F0  | `paired_paths()`：test ↔ src 同 stem（`design.file_plan`）              |
| F1  | `tests_missing[]`                                                   |
| F2  | `review.findings[].file`（Reviewer 打回且 `developer_fix` / `blocking`） |


兜底帧无栈序时，一律按 `root_cause` 入队，按 F0→F2 占预算。

**`paired_paths()`（F0）：** test 路径（`tests/`、`test_*.py`、`*_test.go` 等）↔ 同 stem 的 src/实现文件，依据 `design.file_plan` 与 `dev_manifest.changed_files`；不猜测不存在的路径。

### 6.6 Reviewer 打回（测试已通过）

触发：`review.approved=false` 且 `next_stage=developer`（`test_report.passed` 可能仍为 `true`）。

| 输入来源 | 行为 |
|----------|------|
| `review_feedback.findings[]` | 带 `file` 的 finding → 作为帧入队（无 `line` 则只给文件级 hunk 或模块头） |
| `test_report` | 通常无 failures；**不强制** `failure_contexts` 非空 |
| `retry_cause` | `review_rejection` 或 `both`（若测试也未通过） |

此类重试以 **Review 摘要 + finding 指向的文件** 为主，call-path 为辅。

---

## 7. Prompt 上下文形状

```json
{
  "impl_mode": "retry_patch",
  "impl_retry_count": 1,
  "prd": {},
  "design": {},
  "profile": {},
  "retry_bundle": {
    "retry_cause": "qa_failure",
    "test_report": { "passed": false, "summary": {}, "failures": [], "tests_missing": [] },
    "dev_manifest": {},
    "failure_contexts": [
      {
        "test_id": "tests.test_calc::test_mixed",
        "message": "ValueError: ...",
        "traceback_parse_ok": true,
        "call_path": [
          { "order": 0, "role": "root_cause", "file": "src/calc_core.py", "line": 102, "function": "_parse" },
          { "order": 1, "role": "caller", "file": "src/calc_core.py", "line": 45, "function": "evaluate" },
          { "order": 2, "role": "test", "file": "tests/test_calc.py", "line": 14, "function": "test_mixed" }
        ],
        "snippets": [
          { "path": "src/calc_core.py", "function": "_parse", "frame_order": 0, "content": "def _parse(...): ..." }
        ],
        "omitted_frames": [
          { "file": "tests/test_calc.py", "function": "test_mixed", "reason": "budget_exhausted" }
        ]
      }
    ]
  }
}
```


| 字段             | 首轮        | 重试                    |
| -------------- | --------- | --------------------- |
| `impl_mode`    | `initial` | `retry_patch`         |
| `retry_bundle` | 无         | 有（**无**内嵌 prd/design） |

**`extra_system`（与 JSON 分工）：** 短摘要行动项——`format_qa_retry_feedback`（失败统计、tests_missing 路径）；`format_review_retry_feedback`（blocking findings）。详细栈与函数体**仅**在 `failure_contexts`，避免双份长文本。

---

## 8. Patch 输出（D7）


| 轮次                     | LLM 契约            | 引擎                                           |
| ---------------------- | ----------------- | -------------------------------------------- |
| `impl_retry_count = 0` | 全部 `source_files` | 全量写盘                                         |
| `impl_retry_count > 0` | **仅**新建/修改的文件     | merge 写盘；`change_type` = `create` / `modify` |


- **模块：** `developer_output.apply_developer_output(..., patch_only=True)`
- **Prompt：** `developer.txt` 在 `impl_mode=retry_patch` 时声明「勿重发未改动文件」
- **`tasks_completed`：** 申报当前已满足的全部 `dev_task` id（含历史轮次）

---

## 9. 可观测性


| 事件                         | 行为                            |
| -------------------------- | ----------------------------- |
| `omitted_frames` 非空        | `WARN` + 写入 `FailureContext`  |
| `traceback_parse_ok=false` | `WARN` + 失败闭包兜底               |
| 文件级预算触顶                    | `code_snippets_omitted_paths` |


---

## 10. 实施分期（已完成）


| 阶段     | 状态 | 解决问题           | 交付 |
| ------ | ---- | -------------- | ---- |
| **R0** | ✅ | §1.1 Token（快赢） | D6 Bundle 瘦身 + D7 patch 写盘 + `impl_mode`（**五语言共用**） |
| **R1a** | ✅ | Parser 前置 | `go_json` 解析器 + `cargo_json`/`forge_json` 补强 `output`/`file`/`line` |
| **R1b** | ✅ | §1.2 输入（主路径） | `tools/traceback/*`（五语言）+ `snippet_extract` + 预算 + `failure_contexts` |
| **R2** | ✅ | §1.2 输入（兜底） | 失败闭包、tests_missing、review_feedback（五语言共用） |

**建议 PR 顺序：** **R0 → R1a → R1b → R2**。

**分期依赖说明：**

- **R0** 与语言无关，应最先落地（立刻降 Token）。
- **R1b** 交付时须至少含 **F0 最小闭包**（`failure.file`+`line`），否则 Tier B/C 在 R2 前 `failure_contexts` 可能为空；R2 补全 paired_paths / tests_missing / review_feedback。
- **R1a** 为 Go 及 Rust/Solidity 栈文本的阻塞依赖。

---

## 11. 模块落点


| 模块 | 职责 |
|------|------|
| `tools/traceback/parse.py` | 按 `profile.language` 分发 |
| `tools/traceback/python.py` | pytest traceback |
| `tools/traceback/java.py` | JVM stack (`at pkg.Class.method(File.java:line)`) |
| `tools/traceback/rust.py` | panic / rust test backtrace |
| `tools/traceback/go.py` | go test 失败栈 |
| `tools/traceback/solidity.py` | forge revert / panic 文本（Tier C） |
| `tools/snippet_extract.py` | 按语言定界函数体 / fallback hunk |
| `tools/test_parsers/go_json.py` | **R1a**：Go 测试 JSON 解析 |
| `retry_context.py` | `build_failure_contexts()`、预算分配 |
| `prompt_context.py` | 瘦身 `RetryBundle`、`impl_mode` |
| `developer_output.py` | `patch_only` 写盘 |
| `agents/llm/prompt/validation_feedback.py` | QA / Review 重试摘要 |


`prompt_context_trim.py`：**不再**对 snippet 做头截断（提取阶段已预算化）。

---

## 12. 测试与验收


| ID  | 场景                  | 断言                                       |
| --- | ------------------- | ---------------------------------------- |
| T1  | R0：重试 context       | `retry_bundle` 无 `prd`/`design`；顶层各一份    |
| T2  | R0：patch 写盘         | 仅返回路径被写入；`modify` 正确                     |
| T3  | R1b：Python traceback | `call_path` ≥2 帧；含 root_cause 函数 snippet |
| T3b | R1b：Java junit | 自 `failure.output` 解析 ≥1 用户帧 |
| T3c | R1b：Rust cargo | panic 文本解析或闭包；`failure.output` 非空 |
| T3d | R1b：Go | `go_json` 失败用例含 `file`/`output`；栈或 hunk |
| T3e | R1b：Solidity forge | `failure_contexts` 非空；无栈时闭包 + hunk |
| T4  | R1b：长函数（>200 行）   | `truncated=true`；snippet 为 `line` **前 100 + 后 20** 行 |
| T4b | R1b：无法定界             | snippet 为 `line` 前 80 + 后 20 行（非对称）        |
| T5  | R1b：预算触顶             | `omitted_frames` 非空                      |
| T6  | R2：无 output         | `traceback_parse_ok=false`；闭包配对 src      |
| T7  | R2：Review 打回       | `retry_cause=review_rejection`；finding 文件有 snippet |


**合并验收：**

- [x] §1.1：重试 Bundle 瘦身 + patch-only 写盘（单元测试 T1/T2）
- [x] §1.2：`failure_contexts` 构建（Python traceback、闭包、预算；T3–T5）
- [x] §1.2：五 Profile prompt 与 parser 注册（`go_json` 等）
- [x] §1.3：重试不重写未返回的文件（`patch_only=True`）
- [x] Reviewer 打回：`review_feedback` 注入且 finding 文件可生成 snippet（T7）
- [x] `pytest -q` 全绿（不含 `tests/integration/`）
- [ ] §1.1：重试 completion Token 显著低于首轮（`llm_usage.json` live 度量，待运营验证）
- [ ] §9：`omitted_frames` / `traceback_parse_ok=false` 的 WARN 日志

---

## 14. 审查记录（2026-07-11）

| 维度 | 结论 |
|------|------|
| **合理性** | 问题→举措→分期闭环清晰；非对称 hunk、call-path、patch 三者互补，工程上可落地 |
| **完备性** | 五语言分级、预算、Schema、验收已覆盖；[multi-agent-pipeline-design.md §4.5.1](./multi-agent-pipeline-design.md#451-developer-重试retrybundleexecutable-feedback) 已同步 |
| **已知限制** | Tier C（Solidity）call-path 弱，靠闭包+hunk；Java/Rust/Go 函数定界为 fallback hunk（无 AST/启发式定界）；§9 WARN 日志未落地 |
| **残余风险** | 同一文件多帧重复读盘（可接受）；`test_report.failures` 与 `failure_contexts` 仍有 test_id/message 轻量重复（可接受） |

---

## 13. 废弃（勿实现）

- 固定每文件行数头截断（如 `MAX_SNIPPET_LINES=500`）
- 仅以 `failures[].file` 读整文件、无 call-path
- 对称 `line ± N` 作为**唯一** fallback（已改为前 80 / 后 20 非对称 hunk）
- `retry_bundle` 内嵌 `prd`/`design`
- 扁平 `code_snippets[]` 作为唯一形态（由 `failure_contexts` 取代）

---

**一句话：** 重试 = **输入**（调用路径函数体 + 瘦身 Bundle + 全局预算）+ **输出**（patch-only），分别对应 Token、完备性、防回归三类问题。