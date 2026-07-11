# Artifact Templates — 人读产物格式规范

## 依赖上游文档（只读）

审查 / 修订本目录人读格式时 **仅以本表及正文写作规范为准**。`artifact-schemas/`、`quality-gates/` 为**下游**，由彼引用本目录，不在此表列出（见 [README.md §单向依赖](../README.md#1-单向依赖)）。本目录各 `*-prd.md` 文首依赖表 **一般**列出总设计 + 流水线更早阶段的**上游人读模板**（分类 **上游模板**；见 [pipeline README §文首依赖表](../README.md#3-文首依赖表)）。


| 分类      | 上游文档                                                                | 定位              |
| ------- | ------------------------------------------------------------------- | --------------- |
| **总设计** | [multi-agent-pipeline-design.md](../multi-agent-pipeline-design.md) | 系统的总体设计书 |


---

> **状态：** 定稿（本目录 `*-prd.md`）  
> **设计文档（非 run 落盘）。** 运行时渲染结果见 `docs/runs/<task_id>/prd.md` 等。  
> **JSON 字段规格（机器）：** [`../artifact-schemas/`](../artifact-schemas/README.md)  
> **程序校验规则：** [quality-gates/](../quality-gates/README.md)

---

## 命名约定

本目录文件名后缀 **`-spec`** 表示 **格式规范**（定章节、必填项、写作约束），**不是** Run 落盘 basename。

```text
artifact-templates/{name}-prd.md  →  人读产物格式规范（本目录）
docs/runs/<task_id>/{basename}      →  单次 run 渲染结果（由实现决定）
```

| 格式规范（本目录） | Run 落盘 | 说明 |
|--------------------|----------|------|
| [`prd-spec.md`](./prd-spec.md) | `prd.md` | PM 需求 / PRD（中文） |
| [`design-spec.md`](./design-spec.md) | `design.md` | Architect 设计文档（中文 §1–§6 + 附录 A–D） |
| [`flow-spec.md`](./flow-spec.md) | `*.mmd` | Mermaid 时序 / 流程 / 架构图 |
| [`review-spec.md`](./review-spec.md) | `review.md` | Reviewer 审查摘要（中文） |
| [`dev-principles-spec.md`](./dev-principles-spec.md) | —（约束 `{code_root}/**`） | Developer 跨语言工程原则（README、SRP 等） |

与 [`../artifact-schemas/`](../artifact-schemas/README.md) **姊妹目录、同名 `-spec`**：`artifact-schemas/*-prd.md` = JSON 契约，`artifact-templates/*-prd.md` = 人读格式。

| 层级 | 目录 | 消费者 |
|------|------|--------|
| **机器可读** | `artifact-schemas/*-prd.md` → Run `.json` | Agent 节点、validate、路由 |
| **格式规范** | `artifact-templates/*-prd.md`（本目录） | 渲染器、HITL、文档作者 |
| **校验规则** | [quality-gates/](../quality-gates/README.md) | `prd_validate` / `design_validate` |
| **运行时产物** | `docs/runs/<task_id>/` | 单次 run 落盘 |

---

## 规范索引（定稿）

| 文档 | 对应 JSON / Schema | 生产者（role_id） | 要点 |
|------|-------------------|-------------------|------|
| [prd-spec.md](./prd-spec.md) | [artifact-schemas/prd-spec.md](../artifact-schemas/prd-spec.md) · `prd.json` | PM（`pm`） | FEAT / US / REQ / AC；§9 非功能性需求 |
| [design-spec.md](./design-spec.md) | [artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md) · `design.json` | Architect（`architect`） | 模块 API、错误码、§6 测试用例；**不含 Rollout** |
| [flow-spec.md](./flow-spec.md) | `design.json` → `diagrams[]` | Architect（`architect`） | sequence + flowchart；US 可追溯；`architecture-*.mmd` |
| [review-spec.md](./review-spec.md) | [artifact-schemas/review-spec.md](../artifact-schemas/review-spec.md) · `review.json` | Reviewer（`reviewer`） | `approved` / `next_stage`；AC 全覆盖 |
| [dev-principles-spec.md](./dev-principles-spec.md) | —（约束 `code_root`） | Developer（`developer`） | README、SRP、测试纪律；注入 `developer-principles-snippet.txt` |

**上下游关系：**

```text
prd-spec.md (prd.md)
    ↓
design-spec.md (design.md) + flow-spec.md (*.mmd)
    ↓
dev-principles-spec.md（code_root 工程原则；Developer prompt 注入）
    ↓
（实现 / QA / test_report）
    ↓
review-spec.md (review.md)
```

---

## Run 落盘对照

| Run 文件 | 格式规范 | JSON 契约 | 生产者 |
|----------|----------|-----------|--------|
| `prd.json` | — | [artifact-schemas/prd-spec.md](../artifact-schemas/prd-spec.md) | PM |
| `prd.md` | [prd-spec.md](./prd-spec.md) | 同上 | PM |
| `design.json` | — | [artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md) | Architect |
| `design.md` | [design-spec.md](./design-spec.md) | 同上 | Architect |
| `*.mmd` | [flow-spec.md](./flow-spec.md) | `design.json` → `diagrams[]` | Architect |
| `review.json` | — | [artifact-schemas/review-spec.md](../artifact-schemas/review-spec.md) | Reviewer |
| `review.md` | [review-spec.md](./review-spec.md) | 同上 | Reviewer |

---

## 生成原则

1. **先 JSON，后 MD / Mermaid**：Structured Output（Pydantic）为准，再渲染人读文档。
2. **同源一致**：Run MD / Mermaid 中的 id 须与 JSON 完全一致（见 quality-gates）。
3. **下游不依赖 MD**：Developer / QA / 路由只读 `.json`（Review 图路由读 `review.json`）；Developer 另遵 [dev-principles-spec.md](./dev-principles-spec.md) 与语言 style snippet。
4. **Run 语言**：PRD / Design / Review 人读文档 **中文**；标识符（`FEAT-*`、`ERR-*`、`TC-*` 等）保留英文。

---

## 实现落点（P1）

| Run 产物 | 渲染器 / 写出 |
|----------|----------------|
| `prd.md` | `renderers/prd_md.py` |
| `design.md` | `renderers/design_md.py` |
| `*.mmd` | Architect 节点 / `design.json` |
| `review.md` | `renderers/review_md.py` |
