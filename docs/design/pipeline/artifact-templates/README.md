# Artifact Templates — 人读产物格式规范

> **状态：** 定稿（本目录 `*-spec.md`）  
> **设计文档（非 run 落盘）。** 运行时渲染结果见 `docs/runs/<task_id>/spec.md` 等。  
> **JSON 字段规格（机器）：** [`../artifact-schemas/`](../artifact-schemas/README.md)  
> **程序校验规则：** [quality-gates.md](../quality-gates.md)

---

## 命名约定

本目录文件名后缀 **`-spec`** 表示 **格式规范**（定章节、必填项、写作约束），**不是** Run 落盘 basename。

```text
artifact-templates/{name}-spec.md  →  人读产物格式规范（本目录）
docs/runs/<task_id>/{basename}      →  单次 run 渲染结果（由实现决定）
```

| 格式规范（本目录） | Run 落盘 | 说明 |
|--------------------|----------|------|
| [`prd-spec.md`](./prd-spec.md) | `spec.md` | PM 需求 / PRD（中文） |
| [`design-spec.md`](./design-spec.md) | `design.md` | Architect 设计文档（中文 §1–§10 + 附录） |
| [`flow-spec.md`](./flow-spec.md) | `*.mmd` | Mermaid 时序 / 流程 / 架构图 |
| [`review-spec.md`](./review-spec.md) | `review.md` | Reviewer 审查摘要（中文） |

与 [`../artifact-schemas/`](../artifact-schemas/README.md) **姊妹目录、同名 `-spec`**：`artifact-schemas/*-spec.md` = JSON 契约，`artifact-templates/*-spec.md` = 人读格式。

| 层级 | 目录 | 消费者 |
|------|------|--------|
| **机器可读** | `artifact-schemas/*-spec.md` → Run `.json` | Agent 节点、validate、路由 |
| **格式规范** | `artifact-templates/*-spec.md`（本目录） | 渲染器、HITL、文档作者 |
| **校验规则** | `quality-gates.md` | `spec_validate` / `design_validate` |
| **运行时产物** | `docs/runs/<task_id>/` | 单次 run 落盘 |

---

## 规范索引（定稿）

| 文档 | 对应 JSON / Schema | 生产者（role_id） | 要点 |
|------|-------------------|-------------------|------|
| [prd-spec.md](./prd-spec.md) | [artifact-schemas/prd-spec.md](../artifact-schemas/prd-spec.md) · `spec.json` | PM（`pm`） | FEAT / US / REQ / AC；§9 档位无具体数值 |
| [design-spec.md](./design-spec.md) | [artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md) · `design.json` | Architect（`architect`） | 模块 API、错误码、附录 D 测试；**不含 Rollout** |
| [flow-spec.md](./flow-spec.md) | `design.json` → `diagrams[]` | Architect（`architect`） | sequence + flowchart；US 可追溯；`architecture-*.mmd` |
| [review-spec.md](./review-spec.md) | [artifact-schemas/review-spec.md](../artifact-schemas/review-spec.md) · `review.json` | Reviewer（`reviewer`） | `approved` / `next_stage`；AC 全覆盖 |

**上下游关系：**

```text
prd-spec.md (spec.md)
    ↓
design-spec.md (design.md) + flow-spec.md (*.mmd)
    ↓
（实现 / QA / test_report）
    ↓
review-spec.md (review.md)
```

---

## Run 落盘对照

| Run 文件 | 格式规范 | JSON 契约 | 生产者 |
|----------|----------|-----------|--------|
| `spec.json` | — | [artifact-schemas/prd-spec.md](../artifact-schemas/prd-spec.md) | PM |
| `spec.md` | [prd-spec.md](./prd-spec.md) | 同上 | PM |
| `design.json` | — | [artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md) | Architect |
| `design.md` | [design-spec.md](./design-spec.md) | 同上 | Architect |
| `*.mmd` | [flow-spec.md](./flow-spec.md) | `design.json` → `diagrams[]` | Architect |
| `review.json` | — | [artifact-schemas/review-spec.md](../artifact-schemas/review-spec.md) | Reviewer |
| `review.md` | [review-spec.md](./review-spec.md) | 同上 | Reviewer |

---

## 生成原则

1. **先 JSON，后 MD / Mermaid**：Structured Output（Pydantic）为准，再渲染人读文档。
2. **同源一致**：Run MD / Mermaid 中的 id 须与 JSON 完全一致（见 quality-gates）。
3. **下游不依赖 MD**：Developer / QA / 路由只读 `.json`（Review 图路由读 `review.json`）。
4. **Run 语言**：PRD / Design / Review 人读文档 **中文**；标识符（`FEAT-*`、`ERR-*`、`TC-*` 等）保留英文。

---

## 实现落点（P1）

| Run 产物 | 渲染器 / 写出 |
|----------|----------------|
| `spec.md` | `renderers/spec_md.py` |
| `design.md` | `renderers/design_md.py` |
| `*.mmd` | Architect 节点 / `design.json` |
| `review.md` | `renderers/review_md.py` |
