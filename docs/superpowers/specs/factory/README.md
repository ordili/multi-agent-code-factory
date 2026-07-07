# 工厂设计 — 细目索引

> **主线文档：** [multi-agent-pipeline-design.md](../multi-agent-pipeline-design.md)（流程、路由、目录、验收）  
> **本目录：** Profile、结构化产物、示例与参考的 **详细规格**，避免主线文档过长。

---

## 文档地图

| 文档 | 内容 | 实现真源 |
|------|------|----------|
| [profiles.md](./profiles.md) | Profile 字段、Toolchain、Parser、多语言矩阵 | [`multi_agent_code_factory/profiles/`](../../../../multi_agent_code_factory/profiles/) |
| [artifacts/README.md](./artifacts/README.md) | 产物三层分工 + Run 对照 | — |
| [artifacts/schemas/](./artifacts/schemas/README.md) | **机器可读** JSON 字段规格 | [`multi_agent_code_factory/schemas/`](../../../../multi_agent_code_factory/schemas/) |
| [artifacts/format-to-human/](./artifacts/format-to-human/README.md) | **给人看** 的文档章节模板 | `multi_agent_code_factory/renderers/`（P0） |
| [examples/](./examples/README.md) | JSON / Mermaid **示例片段**（Todo 等） | — |
| [references/](./references/README.md) | 术语、MetaGPT、开源调研 | — |
| [quality-gates.md](./quality-gates.md) | **程序校验** rule_id、`validation` 配置 | `validators/`、`nodes/` |

### Schema 细目（`artifacts/schemas/`）

| 文档 | Schema | 代码 |
|------|--------|------|
| [spec.md](./artifacts/schemas/spec.md) | `SpecArtifact` | `schemas/spec.py` |
| [design.md](./artifacts/schemas/design.md) | `DesignArtifact` | `schemas/design.py` |
| [dev-manifest.md](./artifacts/schemas/dev-manifest.md) | `DevManifest` | `schemas/dev_manifest.py` |
| [test-report.md](./artifacts/schemas/test-report.md) | `TestReport` | `schemas/test_report.py` |
| [review.md](./artifacts/schemas/review.md) | `ReviewReport` | `schemas/review.py` |
| [validation-report.md](./artifacts/schemas/validation-report.md) | `ValidationReport` | `schemas/validation_report.py` |
| [hitl.md](./artifacts/schemas/hitl.md) | `HitlDecision` | `schemas/hitl.py` |
| [run-meta.md](./artifacts/schemas/run-meta.md) | `RunMeta` | `schemas/run_meta.py` |

### 给人看（`artifacts/format-to-human/`）

| 文档 | Run 文件 |
|------|----------|
| [spec.md](./artifacts/format-to-human/spec.md) | `spec.md` |
| [design.md](./artifacts/format-to-human/design.md) | `design.md` |
| [flow.md](./artifacts/format-to-human/flow.md) | `flow.mmd` |
| [review.md](./artifacts/format-to-human/review.md) | `review.md` |

**Agent 角色命名：** [§3.1](../multi-agent-pipeline-design.md#31-角色命名约定)

**阅读顺序：** 主线 §1–§4、§6 → 本目录按需查表；抄 JSON 示例 → [examples/](./examples/README.md)。
