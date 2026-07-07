# format-to-human — 给人看的文档格式

> **与机器可读规格的区别：** 本目录定义 **run 目录下 `.md` / `.mmd` 文件** 的章节、标题与渲染约定（HITL / 人工阅读）。  
> **JSON 字段规格（机器）** 见 [`../schemas/`](../schemas/README.md)。  
> **程序校验规则** 见 [quality-gates.md](../../quality-gates.md)。

## 命名约定

**文件名与 Run 人读产物 basename 一致**（扩展名按实际类型：`.md` 或 `.mmd` 的说明用 `.md`）：

| 本目录（格式规格） | Run 落盘（渲染结果） |
|--------------------|----------------------|
| `spec.md` | `spec.md` |
| `design.md` | `design.md` |
| `flow.md` | `flow.mmd`（Mermaid 源码；规格文档本身是 Markdown，故用 `.md`） |
| `review.md` | `review.md` |

与 [`../schemas/`](../schemas/) 下同名文件（如 `spec.md`）**不冲突**：目录 `schemas/` = JSON 字段；`format-to-human/` = 人读章节模板。引用时写全路径。

## 文档分层

| 层级 | 目录 / 文件 | 消费者 |
|------|-------------|--------|
| **机器可读** | `../schemas/*.md` → Run 的 `.json` | Agent 节点、validate、路由 |
| **给人看** | `format-to-human/*.md`（本目录）→ Run 的 `spec.md` 等 | HITL 审批人、开发者浏览 |
| **校验规则** | `../../quality-gates.md` | `spec_validate` / `design_validate` |
| **运行时产物** | `docs/factory/runs/<task_id>/` | 单次 run 落盘 |

## 索引

| Run 文件 | 格式规格 | 对应 JSON | 生产者（role_id） |
|----------|----------|-----------|-------------------|
| `spec.md` | [spec.md](./spec.md) | `spec.json` | PM（`pm`） |
| `design.md` | [design.md](./design.md) — Design Doc + **依赖/表结构/双图/用例/事务/错误码** | `design.json` | Architect（`architect`） |
| `flow.mmd` | [flow.md](./flow.md) | `design.json` → `diagrams[]` | Architect（`architect`） |
| `review.md` | [review.md](./review.md) | `review.json` | Reviewer（`reviewer`） |

## 生成原则

1. **先 JSON，后 MD**：PM / Architect 先产出 Structured Output（Pydantic），再 **渲染** 人读文档；禁止只写 MD 再反解析 JSON。
2. **同源一致**：MD 中的 `US-*`、`REQ-*`、`AC-*`、`T*` 等 id 须与 JSON 完全一致（`spec_validate` / `design_validate` 可抽检，见 quality-gates §3.3、§4.3）。
3. **下游不依赖 MD**：Developer / QA 等节点只读 `.json`；本目录规格仅约束给人看的文件。
