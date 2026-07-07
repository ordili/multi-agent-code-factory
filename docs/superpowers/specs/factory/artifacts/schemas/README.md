# JSON 规格 — 机器可读（schemas）

> **给人看的文档格式：** [`../format-to-human/`](../format-to-human/README.md)（`spec.md`、`design.md`…）  
> **实现真源：** [`multi_agent_code_factory/schemas/`](../../../../../multi_agent_code_factory/schemas/)（Pydantic v2）  
> **校验规则：** [quality-gates.md](../../quality-gates.md)

## 命名约定

设计 Spec 文件名 **对齐** `multi_agent_code_factory/schemas/<module>.py`（kebab-case）：

| Pydantic / 模块 | 设计 Spec 文档 | Run 机器文件 |
|-----------------|----------------|--------------|
| `SpecArtifact` / `spec.py` | [spec.md](./spec.md) | `spec.json` |
| `DesignArtifact` / `design.py` | [design.md](./design.md) | `design.json` |
| `DevManifest` / `dev_manifest.py` | [dev-manifest.md](./dev-manifest.md) | `dev_manifest.json` |
| `TestReport` / `test_report.py` | [test-report.md](./test-report.md) | `test_report.json` |
| `ReviewReport` / `review.py` | [review.md](./review.md) | `review.json` |
| `ValidationReport` / `validation_report.py` | [validation-report.md](./validation-report.md) | `spec_validation.json` / `design_validation.json` |
| `HitlDecision` / `hitl.py` | [hitl.md](./hitl.md) | `hitl.json` |
| `RunMeta` / `run_meta.py` | [run-meta.md](./run-meta.md) | `run_meta.json` |

**注意：** Run 目录下的 `spec.md`、`design.md` 是 **运行时人读产物**，与设计 Spec 路径 `factory/artifacts/schemas/spec.md`（本文档）不同。

## 索引

| Schema | 人读格式 | 细目 |
|--------|----------|------|
| `SpecArtifact` | [format-to-human/spec.md](../format-to-human/spec.md) | [spec.md](./spec.md) |
| `DesignArtifact` | [format-to-human/design.md](../format-to-human/design.md) + [flow.md](../format-to-human/flow.md) | [design.md](./design.md) |
| `DevManifest` | — | [dev-manifest.md](./dev-manifest.md) |
| `TestReport` | — | [test-report.md](./test-report.md) |
| `ReviewReport` | [format-to-human/review.md](../format-to-human/review.md) | [review.md](./review.md) |
| `ValidationReport` | — | [validation-report.md](./validation-report.md) |
| `HitlDecision` | — | [hitl.md](./hitl.md) |
| `RunMeta` | — | [run-meta.md](./run-meta.md) |
