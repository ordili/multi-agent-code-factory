# Artifact Schemas — 机器可读 JSON 规格

## 依赖上游文档（只读）

审查 / 修订本目录 JSON 契约时 **以本表、正文字段定义及同名上游人读 § 映射为准**。`quality-gates/`、`examples/` 为**下游**，不在此表列出（见 [README.md §单向依赖](../README.md#1-单向依赖)）。


| 分类       | 上游文档                                                         | 定位                    |
| -------- | ------------------------------------------------------------ | --------------------- |
| **总设计**  | [multi-agent-pipeline-design.md](../multi-agent-pipeline-design.md) | 系统的总体设计书 |
| **索引**   | [README.md](../README.md)                           | 目录职责与文档单向依赖           |
| **类型实现** | `multi_agent_code_factory/schemas/`                          | Pydantic 定义（以实现为准）    |


---

> **状态：** 定稿（本目录 `*-prd.md`）  
> **索引：** [README.md](../README.md)（目录职责、文档单向依赖规则）  
> **设计文档（非 run 落盘）。** 运行时实例见 `docs/runs/<task_id>/*.json`。  
> **类型定义以：** [`multi_agent_code_factory/schemas/`](../../../../multi_agent_code_factory/schemas/)（Pydantic v2）**为准**

本目录 **只定义 Run `*.json` 的字段与类型**。校验规则（`PRD-*` / `DES-*`）、示例片段分别在 **`quality-gates/`**、**`examples/`** ——由下游引用本文。人读格式（`prd.md`、`design.md` 等）为 **同名上游** `artifact-templates/*-prd.md`（JSON ↔ 人读 § 映射，列入各 spec 依赖表）；章节写法 **不在本文展开**（见 [README.md §单向依赖](../README.md#1-单向依赖)）。

---

## 命名约定

本目录文件名后缀 **`-spec`** 表示 **JSON 契约规格**（字段、枚举、示例），**不是** Run 落盘 basename。

```text
artifact-schemas/{name}-prd.md  →  JSON 契约设计说明（本目录）
docs/runs/<task_id>/{file}.json   →  单次 run 落盘
```

Pydantic 模块对齐：`schemas/<module>.py`（snake_case）；设计 Spec 文档为 kebab-case + `-spec` 后缀。

---

## 契约索引

| Pydantic 模型 | 契约文档 | Run 落盘 | 流水线阶段（上游 → 本产物） |
|---------------|----------|----------|----------------------------|
| `PrdArtifact` | [prd-spec.md](./prd-spec.md) | `prd.json` | PM |
| `DesignArtifact` | [design-spec.md](./design-spec.md) | `design.json` | Architect；上游 [prd-spec.md](./prd-spec.md) |
| `DevManifest` | [dev-manifest-spec.md](./dev-manifest-spec.md) | `dev_manifest.json` | Developer；上游 `design.json` |
| `TestReport` | [test-report-spec.md](./test-report-spec.md) | `test_report.json` | QA |
| `ReviewReport` | [review-spec.md](./review-spec.md) | `review.json` | Reviewer |
| `ValidationReport` | [validation-report-spec.md](./validation-report-spec.md) | `prd_validation.json` / `design_validation.json` | `*_validate` 节点产出 |
| `HitlDecision` | [hitl-spec.md](./hitl-spec.md) | `hitl.json` | `*_hitl` / `escalation_hitl` |
| `RunMeta` | [run-meta-spec.md](./run-meta-spec.md) | `run_meta.json` | 每次 run 元数据 |

**`diagrams[]`：** 定义在 [design-spec.md](./design-spec.md)；Run 配套 `*.mmd` 文件与 `diagrams[].path` 一致。

---

## 文档规则（本目录）

| 规则 | 说明 |
|------|------|
| **只写 JSON** | 字段、类型、枚举、标识符、嵌套结构、JSON 示例 |
| **只引上游** | 如 [design-spec.md](./design-spec.md) 引用 [prd-spec.md](./prd-spec.md)；同名 [artifact-templates/*-prd.md](../artifact-templates/) 列入依赖表（**人读模板**）；不引 `quality-gates/` |
| **不写人读章节** | Run Markdown / Mermaid 章节正文、写作约束在 `artifact-templates/`；schema 只引 § 映射，不展开章节写法 |
| **不写 rule_id 清单** | `PRD-*` / `DES-*` 的触发条件与判定 → **`quality-gates/`**（规则正文所在层） |
| **姊妹目录与全库地图** | 见 [README.md](../README.md) |
