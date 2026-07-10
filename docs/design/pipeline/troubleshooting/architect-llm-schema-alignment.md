# LLM 输出格式对照

> **场景：** 2026-07-10 · Live + DeepSeek + `prompted_json` · 计算器 CLI 任务  
> **范围：** 日志中实际出现偏差的字段

---

## 1. PM — `SpecArtifact`

### 探测脚本（查看实际输入 / 输出）

与 pipeline `run_pm` live 路径相同方式组装 prompt，单次调用 LLM 并落盘：

```bash
python scripts/debug_pm_spec_llm.py
python scripts/debug_pm_spec_llm.py --dry-run
python scripts/debug_pm_spec_llm.py --show-prompts
```

要求格式与 system 末尾 Example 均在脚本内 ``REQUIRED_FORMAT_SNIPPET``（含 ``success_metrics: []``）；``SYSTEM_PROMPT`` 内联全文（与 ``pm.txt`` + 语言 snippet 对齐，改 pipeline 时需手动同步）。默认只打印模型回复，加 ``--show-prompts`` 才打印 prompt。

### `success_metrics`

| | 格式 |
|---|------|
| **要求** | 对象数组，每项 `{id, name, description, target, verifiable_by}`；**可为 `[]`**（spec.md §4 渲染为「无」） |
| **模型输出（常见）** | 字符串数组，如 `["pytest 测试全部通过"]` |

**分工（prd-spec.md）：**

| 字段 | spec.md 章节 | 写什么 |
|------|--------------|--------|
| `success_metrics` | §4 业务指标（选填） | 业务结果 KPI；小工具宜 `[]` |
| `acceptance_criteria` | §10 验收标准 | 工程门禁（pytest、lint 等） |

```json
// 要求（计算器 — 无业务 KPI）
"success_metrics": [],
"acceptance_criteria": [
  {
    "id": "AC-1",
    "description": "pytest 测试全部通过（覆盖 US-1）",
    "verifiable_by": "automated_test"
  }
]

// 模型输出（错误）
"success_metrics": ["pytest 测试全部通过"]
```

**prompt 修复（2026-07）：** `pm.txt` 已补充 `success_metrics` 对象结构与 KPI/AC 分工；`LlmParseError` 重试会附带校验错误摘要。

**后续审计：** 见 [pm-spec-prompt-audit.md](./pm-spec-prompt-audit.md)（PM 字段 prompt ↔ schema 对照草稿）。

### `operational_profile.user_scale`

| | 格式 |
|---|------|
| **要求** | 枚举之一：`personal` · `team` · `multi_tenant` · `internet` |
| **模型输出** | `single_user` |

```json
// 要求
"operational_profile": {
  "user_scale": "personal",
  "high_concurrency": false,
  "performance": { "tier": "best_effort" }
}

// 模型输出（attempt 1）
"operational_profile": {
  "user_scale": "single_user",
  ...
}
```

---

## 2. Architect — `ArchitectLLMOutput` 顶层

| 字段 | 要求 | 模型输出 |
|------|------|----------|
| `design` | `DesignArtifact` 对象，**必填** | 有（结构见下节） |
| `mmd_files` | `[{ "path", "content" }]`，可选 | （日志未报此项） |
| `flow_mmd` | `string`，可选 | （日志未报此项） |

```json
// 要求
{
  "design": { ... },
  "mmd_files": [{ "path": "flow.mmd", "content": "..." }]
}

// 模型输出
{
  "design": { ... }
}
```

---

## 3. Architect — `design`（`DesignArtifact`）

### 3.1 标识符命名

| 类型 | 要求 | 模型输出 |
|------|------|----------|
| 错误码 | `ERR-{域}-###`，如 `ERR-CALC-001` | `ERR-1`、`ERR-2` |
| 用例 id | `TC-HAP-{域}-###` / `TC-NEG-...` / `TC-BND-...` | `TC-HAP-1`、`TC-NEG-1`、`TC-BND-1` |

### 3.2 `error_catalog[]`

| 字段 | 要求 | 模型输出 |
|------|------|----------|
| `code` | **必填** | **缺失**（用了 `id`） |
| `when` | 可选 | 有 |
| `message` | 可选 | 有 |
| `retryable` | 可选 | 无 |
| `recovery` | 可选 | 无 |
| `id` | 无此字段 | `ERR-1` |
| `severity` | 无此字段 | `error` |

```json
// 要求
"error_catalog": [
  {
    "code": "ERR-CALC-001",
    "when": "除数为 0",
    "message": "除零",
    "retryable": false
  }
]

// 模型输出
"error_catalog": [
  {
    "id": "ERR-1",
    "message": "除法时输入除数为0",
    "severity": "error"
  },
  {
    "id": "ERR-2",
    "message": "...",
    "severity": "error"
  }
]
```

### 3.3 `test_cases[]`

| 字段 | 要求 | 模型输出 |
|------|------|----------|
| `id` | **必填** | 有（简写格式） |
| `kind` | **必填**：`happy` / `negative` / `boundary` | **缺失** |
| `title` | 可选 | 无（部分用 `description`） |
| `description` | 可选 | 有 |
| `expected` | 可选 | 有 |
| `covers` | 可选 `string[]`，宜 `AC-*` | NEG 用 `ERR-1` |
| `error_code` | 可选，NEG 宜填 | 无 |

```json
// 要求
"test_cases": [
  {
    "id": "TC-HAP-CALC-001",
    "kind": "happy",
    "title": "1+1",
    "covers": ["AC-1"]
  },
  {
    "id": "TC-NEG-CALC-001",
    "kind": "negative",
    "title": "除零",
    "error_code": "ERR-CALC-001"
  },
  {
    "id": "TC-BND-CALC-001",
    "kind": "boundary",
    "title": "大数",
    "covers": ["AC-1"]
  }
]

// 模型输出
"test_cases": [
  { "id": "TC-HAP-1", "description": "...", "expected": "返回正确的和" },
  { "id": "TC-HAP-2", "description": "...", "expected": "返回正确的差" },
  { "id": "TC-HAP-3", "description": "...", "expected": "返回正确的积" },
  { "id": "TC-HAP-4", "description": "...", "expected": "返回正确的商" },
  { "id": "TC-HAP-5", "description": "...", "expected": "浮点精度的结果" },
  { "id": "TC-NEG-1", "description": "...", "covers": ["ERR-1"] },
  { "id": "TC-NEG-2", "description": "...", "covers": ["ERR-2"] },
  { "id": "TC-BND-1", "description": "...", "expected": "inf 或正确结果" }
]
```

---

## 4. 其它 `DesignArtifact` 子对象（要求格式摘要）

日志未报 parse 错误，但 Architect 产出须符合下列形状。

### `ModuleSpec`

```json
{ "name": "CalcCore", "path": "src/calc_core.py", "responsibility": "...", "code_domain": "CALC" }
```

### `DevTask`

```json
{ "id": "T1", "path": "src/calc_core.py", "description": "...", "depends_on": [], "covers": ["AC-1"] }
```

### `InterfaceSpec` + `OperationSpec`

```json
{
  "name": "CalcCore",
  "module_ref": "CalcCore",
  "operations": [
    {
      "name": "eval",
      "summary": "求值",
      "inputs": [{ "name": "expr", "type": "string", "required": true }],
      "outputs": [{ "name": "value", "type": "number", "required": true }],
      "errors": ["ERR-CALC-001"]
    }
  ]
}
```

### `ContextView`

```json
{ "actors": ["User", "CalcCLI", "CalcCore"] }
```

### `ArchitectureOverview`

```json
{
  "solution_strategy": "CLI + 纯函数求值",
  "code_delta": { "summary": "空仓库" }
}
```

### `ExternalDependency`

```json
{ "name": "none", "kind": "none", "purpose": "无外部中间件" }
```

### `TraceRow`

```json
{ "spec_ref_id": "AC-1", "spec_ref_kind": "AC", "design_ref": "CalcCore" }
```

### `DiagramRef`

```json
{ "path": "flow.mmd", "kind": "sequence" }
```

---

## 5. 权威定义

| 文档 | 路径 |
|------|------|
| Design JSON 契约 | [artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md) |
| Spec JSON 契约 | [artifact-schemas/prd-spec.md](../artifact-schemas/prd-spec.md) |
| 计算器 fixture 示例 | `tests/fixtures/design-calculator-stateless-min.json` |
