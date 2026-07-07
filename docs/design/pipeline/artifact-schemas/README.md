# Artifact Schemas — 机器可读 JSON 规格

> **设计文档（非 run 落盘）。** 运行时实例见 `docs/runs/<task_id>/*.json`。  
> **人读模板：** [`../artifact-templates/`](../artifact-templates/README.md)  
> **类型定义以：** [`multi_agent_code_factory/schemas/`](../../../../multi_agent_code_factory/schemas/)（Pydantic v2）**为准**；下文为设计说明。  
> **校验规则：** [quality-gates.md](../quality-gates.md)

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

## 索引

| Schema | 人读模板 | 细目 |
|--------|----------|------|
| `SpecArtifact` | [artifact-templates/spec.md](../artifact-templates/spec.md) | [spec.md](./spec.md) |
| `DesignArtifact` | [artifact-templates/design.md](../artifact-templates/design.md) + [flow.md](../artifact-templates/flow.md) | [design.md](./design.md) |
| `DevManifest` | — | [dev-manifest.md](./dev-manifest.md) |
| `TestReport` | — | [test-report.md](./test-report.md) |
| `ReviewReport` | [artifact-templates/review.md](../artifact-templates/review.md) | [review.md](./review.md) |
| `ValidationReport` | — | [validation-report.md](./validation-report.md) |
| `HitlDecision` | — | [hitl.md](./hitl.md) |
| `RunMeta` | — | [run-meta.md](./run-meta.md) |
