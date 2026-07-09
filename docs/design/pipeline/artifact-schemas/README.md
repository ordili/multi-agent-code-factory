# Artifact Schemas — 机器可读 JSON 规格

> **状态：** 定稿（本目录 `*-spec.md`）  
> **设计文档（非 run 落盘）。** 运行时实例见 `docs/runs/<task_id>/*.json`。  
> **人读格式规范：** [`../artifact-templates/`](../artifact-templates/README.md)（同名 `*-spec.md`）  
> **类型定义以：** [`multi_agent_code_factory/schemas/`](../../../../multi_agent_code_factory/schemas/)（Pydantic v2）**为准**  
> **校验规则：** [quality-gates/](../quality-gates/README.md) · [spec-validate](../quality-gates/spec-validate.md) · [design-validate](../quality-gates/design-validate.md)

---

## 命名约定

本目录文件名后缀 **`-spec`** 表示 **JSON 契约规格**（字段、枚举、示例），**不是** Run 落盘 basename。

```text
artifact-schemas/{name}-spec.md  →  JSON 契约设计说明（本目录）
artifact-templates/{name}-spec.md →  人读 Markdown 格式规范（姊妹目录）
docs/runs/<task_id>/{file}.json   →  单次 run 落盘（由实现决定）
```

| 层 | 路径示例 | 内容 | Run 落盘 |
|----|----------|------|----------|
| **JSON 契约** | `artifact-schemas/prd-spec.md` | `SpecArtifact` 字段 | `spec.json` |
| **人读格式** | `artifact-templates/prd-spec.md` | Run `spec.md` 章节 | `spec.md` |

**成对文档**（schemas ↔ templates，同名 `-spec`）：

| Schema | JSON 契约（本目录） | 人读格式（templates） | Run JSON | Run 人读 |
|--------|---------------------|----------------------|----------|----------|
| `SpecArtifact` | [prd-spec.md](./prd-spec.md) | [prd-spec.md](../artifact-templates/prd-spec.md) | `spec.json` | `spec.md` |
| `DesignArtifact` | [design-spec.md](./design-spec.md) | [design-spec.md](../artifact-templates/design-spec.md) + [flow-spec.md](../artifact-templates/flow-spec.md) | `design.json` | `design.md` + `*.mmd` |
| `ReviewReport` | [review-spec.md](./review-spec.md) | [review-spec.md](../artifact-templates/review-spec.md) | `review.json` | `review.md` |

**仅 JSON 契约**（无人读 run template；Developer 实现另遵 [dev-principles-spec.md](../artifact-templates/dev-principles-spec.md)）：

| Schema | JSON 契约 | Run 文件 |
|--------|-----------|----------|
| `DevManifest` | [dev-manifest-spec.md](./dev-manifest-spec.md) | `dev_manifest.json` |
| `TestReport` | [test-report-spec.md](./test-report-spec.md) | `test_report.json` |
| `ValidationReport` | [validation-report-spec.md](./validation-report-spec.md) | `*_validation.json` |
| `HitlDecision` | [hitl-spec.md](./hitl-spec.md) | `hitl.json` |
| `RunMeta` | [run-meta-spec.md](./run-meta-spec.md) | `run_meta.json` |

Pydantic 模块对齐：`schemas/<module>.py`（snake_case）；设计 Spec 文档为 kebab-case + `-spec` 后缀。

---

## 索引

| Schema | 人读格式规范 | JSON 契约 |
|--------|--------------|-----------|
| `SpecArtifact` | [artifact-templates/prd-spec.md](../artifact-templates/prd-spec.md) | [prd-spec.md](./prd-spec.md) |
| `DesignArtifact` | [design-spec.md](../artifact-templates/design-spec.md) + [flow-spec.md](../artifact-templates/flow-spec.md) | [design-spec.md](./design-spec.md) |
| `DevManifest` | [dev-principles-spec.md](../artifact-templates/dev-principles-spec.md)（工程原则，非 JSON） | [dev-manifest-spec.md](./dev-manifest-spec.md) |
| `TestReport` | — | [test-report-spec.md](./test-report-spec.md) |
| `ReviewReport` | [review-spec.md](../artifact-templates/review-spec.md) | [review-spec.md](./review-spec.md) |
| `ValidationReport` | — | [validation-report-spec.md](./validation-report-spec.md) |
| `HitlDecision` | — | [hitl-spec.md](./hitl-spec.md) |
| `RunMeta` | — | [run-meta-spec.md](./run-meta-spec.md) |
