# Artifact Templates — 给人看的文档格式

> **设计文档（非 run 落盘）。** 运行时渲染结果见 `docs/runs/<task_id>/spec.md` 等。  
> **JSON 字段规格（机器）：** [`../artifact-schemas/`](../artifact-schemas/README.md)  
> **程序校验规则：** [quality-gates.md](../quality-gates.md)

## 命名约定

**文件名与 Run 人读产物 basename 一致**：

| 本目录（格式规格） | Run 落盘（渲染结果） |
|--------------------|----------------------|
| `spec.md` | `spec.md` |
| `design.md` | `design.md` |
| `flow.md` | `flow.mmd` |
| `review.md` | `review.md` |

与 [`../artifact-schemas/`](../artifact-schemas/) 下同名文件 **不冲突**：`artifact-schemas/` = JSON 字段；`artifact-templates/` = 人读章节模板。

## 文档分层

| 层级 | 目录 | 消费者 |
|------|------|--------|
| **机器可读** | `../artifact-schemas/*.md` → Run 的 `.json` | Agent 节点、validate、路由 |
| **给人看** | `artifact-templates/*.md`（本目录）→ Run 的 `spec.md` 等 | HITL 审批人、开发者浏览 |
| **校验规则** | `../quality-gates.md` | `spec_validate` / `design_validate` |
| **运行时产物** | `docs/runs/<task_id>/` | 单次 run 落盘 |

## 索引

| Run 文件 | 格式规格 | 对应 JSON | 生产者（role_id） |
|----------|----------|-----------|-------------------|
| `spec.md` | [spec.md](./spec.md) | `spec.json` | PM（`pm`） |
| `design.md` | [design.md](./design.md) | `design.json` | Architect（`architect`） |
| `flow.mmd` | [flow.md](./flow.md) | `design.json` → `diagrams[]` | Architect（`architect`） |
| `review.md` | [review.md](./review.md) | `review.json` | Reviewer（`reviewer`） |

## 生成原则

1. **先 JSON，后 MD**：先 Structured Output（Pydantic），再渲染人读文档。
2. **同源一致**：MD 中的 id 须与 JSON 完全一致（见 quality-gates）。
3. **下游不依赖 MD**：Developer / QA 只读 `.json`。
