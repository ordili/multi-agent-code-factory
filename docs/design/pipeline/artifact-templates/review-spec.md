# review-spec.md — Reviewer 人读摘要格式规范

> **状态：** 定稿 · [artifact-templates 索引](./README.md)  
> **配套规范：** [prd-spec.md](./prd-spec.md) · [design-spec.md](./design-spec.md) · [flow-spec.md](./flow-spec.md) · [dev-principles-spec.md](./dev-principles-spec.md)  
> **节点交接以：** [`../artifact-schemas/review-spec.md`](../artifact-schemas/review-spec.md)（`ReviewReport` / `review.json`）**为准**；本文件定义 Run `review.md` 的章节与写法。  
> **Run 路径：** `docs/runs/<task_id>/review.md`  
> **路由实现：** [multi-agent-pipeline-design.md §4.3](../multi-agent-pipeline-design.md) · `graph_routing.py` → `route_after_review`  
> **校验：** 无独立 `review_validate` 门禁；Pydantic 结构校验 + 路由对 `approved` 的守卫

---

## 文档定位

| 对比 | Reviewer（`reviewer`） | deploy HITL（`deploy_hitl`） |
|------|------------------------|------------------------------|
| 时机 | QA **`test_report` 之后** | Reviewer 路由到 `deploy` **之后** |
| 产物 | `review.json` + `review.md` | `HitlDecision`（人工） |
| 作用 | LLM 对照 spec / design / 测试结论，**决定下一环** | 人工审批 diff、敏感变更 |
| 路由依据 | **`review.json` 的 `next_stage`** | HITL 续跑 / 终止 |

**可信度（流水线）：** `TestReport` > `ValidationReport` > `HitlDecision` > `ReviewReport`（LLM）。`test_report.passed=false` 时 **不得** `approved=true`（见 [Reviewer prompt 约定](#输入与判定依据)）。

**下游：** 图路由 **只读 `review.json`**；Run `review.md` 供 HITL / 人工速读，Developer / QA **不依赖** MD。

---

## 语言与格式（Run `review.md`）

| 项 | 约定 |
|----|------|
| **正文语言** | **中文** — 章节标题、摘要、发现项 `message`、AC 说明 |
| **保留英文** | `AC-*`、`F-*` id；`next_stage` 枚举；`severity` / `category` / `routing` 枚举字面量；文件路径 |
| **章节标题** | 固定 **中文**（见下表） |
| **页脚（渲染器）** | `---` 后一行机器可读摘要：`approved: \`true\`` · `next_stage: \`deploy\``（见 [实现提示](#实现提示)） |

---

## 固定章节

| § | Markdown 标题 | 对应 JSON | 必填 |
|---|---------------|-----------|------|
| — | `# 审查结论` | `approved`、`summary` | ✓ |
| 1 | `## 路由` | `next_stage` | ✓ |
| 2 | `## 验收覆盖` | `acceptance_coverage[]` | ✓（**须覆盖 spec 全部 AC**） |
| 3 | `## 发现项` | `findings[]` | ✓（无则写 **无**） |

JSON 另有 `version: "1"`（MD 页眉 **不渲染**，保留在 `review.json`）。

---

## 各节写法

### 页眉 `# 审查结论`

| 行 | 格式 | JSON |
|----|------|------|
| 通过 | `**通过：** 是` / `否` | `approved` |
| 摘要 | `**摘要：** {一句结论}` | `summary` |

摘要须说清：**测试是否通过、AC 是否满足、是否有 blocking 发现、建议下一环**。

### §1 路由

```markdown
## 路由

下一节点：`{next_stage}`
```

| `next_stage` | 含义 | 图路由（摘要） |
|--------------|------|----------------|
| `deploy` | 审查通过，可进入部署审批 | → `deploy_hitl`（须 **`approved=true`**） |
| `developer` | 实现/测试可修 | → `developer`（实现环） |
| `architect` | 设计/接口/错误码/覆盖缺口 | → `architect`（设计环） |
| `pm` | 需求/验收/范围矛盾 | → `pm`（需求环） |

> **`next_stage=deploy` 不等于已上线** — 仅表示进入 **deploy HITL**；人工仍可读本 `review.md` 与 diff。

**`approved` 与 `next_stage` 须一致：**

| 组合 | 语义 |
|------|------|
| `approved=true` + `deploy` | 正常通过 |
| `approved=false` + `developer` / `architect` / `pm` | 正常打回 |
| `approved=false` + `deploy` | **矛盾输出** — 实现按 [`route_after_review`](../artifact-schemas/review-spec.md#路由route_after_review) **强制回 Developer** |
| `approved=true` + 非 `deploy` | 不推荐；HITL 应以 JSON 为准 |

### §2 验收覆盖

**须列出 `spec.acceptance_criteria[]` 中的每一个 `AC-*`**（与 prompt 一致；不可只写部分 AC）。

| AC | 满足 | 说明 |
|----|------|------|
| AC-1 | ✓ / ✗ | 证据：如 `test_report.passed`、具体用例 id、缺失项 |

JSON：`acceptance_coverage[]` → `{ "id": "AC-1", "met": true|false, "note"?: string }`

- `met=false` 时 `note` **宜** 说明缺什么（未测、失败用例、与 design 不一致等）。
- 无 AC 时（极罕见）写 `—`；JSON 用 `[]`。

### §3 发现项

无发现时正文写 **无**；JSON 用 `findings: []`。

**每条发现（渲染器列表格式，Agent 宜对齐）：**

```markdown
- **F-1** [major/correctness] (blocking) (`src/store.py`): 损坏 JSON 无 ERR-STORE 处理 → `architect_redesign`
- **F-2** [minor/style] (non-blocking): 命名与 design 不一致
```

| 片段 | 来源 |
|------|------|
| `F-{n}` | `findings[].id` — 推荐 `F-1`、`F-2`… 全局递增 |
| `[severity/category]` | 见下表枚举 |
| `(blocking)` / `(non-blocking)` | `findings[].blocking` |
| `` (`path`) `` | 可选 `findings[].file` |
| `message` | 中文或英文均可；宜具体可行动 |
| `→ \`routing\`` | 可选；**仅人读/自检**，**不参与**图路由 |

#### Finding 字段（JSON）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 如 `F-1` |
| `severity` | enum | `critical` \| `major` \| `minor` |
| `category` | enum | `security` \| `performance` \| `correctness` \| `style` |
| `message` | string | 问题描述 |
| `blocking` | boolean | 是否阻断合并/部署 |
| `file` | string? | 相关文件路径 |
| `routing` | enum? | `developer_fix` \| `architect_redesign` \| `pm_scope_change` |

**`routing` vs `next_stage`：** 报告级 **`next_stage` 决定图路由**；单条 `Finding.routing` 供 Reviewer 自检「这条该谁修」，与 `next_stage` 宜一致，但 **路由代码不读 `routing`**（详见 [`artifact-schemas/review-spec.md`](../artifact-schemas/review-spec.md)）。

| `routing`（Finding） | 通常对应的 `next_stage` |
|----------------------|-------------------------|
| `developer_fix` | `developer` |
| `architect_redesign` | `architect` |
| `pm_scope_change` | `pm` |

---

## 通过条件

同时满足（与 schema 一致）：

1. `approved=true`
2. `next_stage=deploy`
3. 无 `severity=critical` **且** `blocking=true` 的发现项
4. `test_report.passed=true`（Reviewer 输入约束）
5. `acceptance_coverage` 中 **全部** AC 的 `met=true`（与 prompt 一致）

存在 `major` + `blocking=true` 时通常 `approved=false` 并路由到对应环节。

---

## 输入与判定依据

Reviewer 上下文（`multi_agent_code_factory/profiles/_shared/prompts/reviewer.txt`）通常包含：

| 输入 | 对照什么 |
|------|----------|
| `spec` | `acceptance_criteria[]`、scope、异常 US |
| `design` | 模块 API、错误码、附录 D 覆盖 |
| `test_report` | `passed`、失败用例、`tests_missing`（对照 [dev-manifest-spec.md](../artifact-schemas/dev-manifest-spec.md) / design 路径） |
| `code_root` / `git_diff` | 实现是否与 design 一致；**README.md** 是否存在且含安装/用法/测试说明（[dev-principles-spec.md](./dev-principles-spec.md)） |
| `dev_manifest` | `tasks_completed` 是否覆盖 P0 `dev_tasks`；`changed_files` 与 design / 实际 diff 是否一致 |

**硬规则：** `test_report.passed=false` → **不得** `approved=true`；`next_stage` 应为 `developer`（或说明需设计/需求环时选 `architect` / `pm`）。

---

## 样例

### 样例 A — 通过（→ deploy HITL）

```markdown
# 审查结论

**通过：** 是  
**摘要：** 测试全部通过，AC 均已满足，无 blocking 发现。

## 路由

下一节点：`deploy`

## 验收覆盖

| AC | 满足 | 说明 |
|----|------|------|
| AC-1 | ✓ | test_report.passed |
| AC-2 | ✓ | 集成测覆盖 US-1～US-3 |

## 发现项

无

---

approved: `true` · next_stage: `deploy`
```

### 样例 B — 打回 Developer（测试/实现）

```markdown
# 审查结论

**通过：** 否  
**摘要：** test_report 失败：除零未返回 ERR-EVAL-001，需修复实现与单测。

## 路由

下一节点：`developer`

## 验收覆盖

| AC | 满足 | 说明 |
|----|------|------|
| AC-1 | ✗ | tests/test_calculator.py::test_divide_by_zero FAILED |
| AC-2 | ✗ | US-4 错误提示未验收 |

## 发现项

- **F-1** [major/correctness] (blocking) (`src/evaluator.py`): `2/0` 抛未捕获异常，未映射 ERR-EVAL-001 → `developer_fix`
- **F-2** [minor/style] (non-blocking) (`src/cli.py`): stderr 文案与 design §6.2 不一致

---

approved: `false` · next_stage: `developer`
```

### 样例 C — 升 Architect（设计缺口）

```markdown
# 审查结论

**通过：** 否  
**摘要：** 设计未覆盖持久化损坏 JSON 的异常路径，AC-2 无法验收。

## 路由

下一节点：`architect`

## 验收覆盖

| AC | 满足 | 说明 |
|----|------|------|
| AC-1 | ✓ | 主路径 CRUD 通过 |
| AC-2 | ✗ | 损坏 store 无对应用例/错误码 |

## 发现项

- **F-1** [major/correctness] (blocking) (`src/todo_store.py`): 缺少 corrupt JSON 的 ERR-STORE 与附录 D 用例 → `architect_redesign`

---

approved: `false` · next_stage: `architect`
```

> 对照 JSON fixture：`tests/fixtures/review-architect.json`

### 样例 D — 升 PM（范围/验收矛盾）

```markdown
# 审查结论

**通过：** 否  
**摘要：** spec 未包含 delete 能力，但 AC-2 要求「完整 CRUD」；需 PM 澄清范围。

## 路由

下一节点：`pm`

## 验收覆盖

| AC | 满足 | 说明 |
|----|------|------|
| AC-2 | ✗ | delete 不在 spec scope_in |

## 发现项

- **F-1** [major/correctness] (blocking): spec scope 与 AC-2 矛盾 → `pm_scope_change`

---

approved: `false` · next_stage: `pm`
```

> 对照 JSON fixture：`tests/fixtures/review-pm.json`

---

## 实现提示

| 组件 | 路径 |
|------|------|
| Schema | `multi_agent_code_factory/schemas/review.py` |
| 渲染器 | `multi_agent_code_factory/renderers/review_md.py` |
| 节点 | `multi_agent_code_factory/agents/reviewer.py` |
| 路由 | `multi_agent_code_factory/graph_routing.py` → `route_after_review` |

渲染器 **须** 输出：中文固定章节 + 发现项列表 + 页脚 `approved` / `next_stage` 行。  
**以 `review.json` 为准**；MD 与 JSON 不一致时，路由与门禁只认 JSON。
