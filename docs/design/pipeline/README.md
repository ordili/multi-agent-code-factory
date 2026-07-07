# 工厂设计 — 细目索引

> **主线文档：** [multi-agent-pipeline-design.md](./multi-agent-pipeline-design.md)（流程、路由、目录、验收）  
> **本目录：** Profile、结构化产物规格、示例与参考的 **详细设计 Spec**，避免主线过长。  
> **V1 范围：** 通用流水线；**V2 领域**见 [domains/](../../../domains/README.md)

---

## 文档地图

| 文档 | 内容 | 代码落点（以实现为准） |
|------|------|----------|
| [profiles.md](./profiles.md) | Profile 字段、Toolchain、Parser、多语言矩阵 | [`multi_agent_code_factory/profiles/`](../../../multi_agent_code_factory/profiles/) |
| [artifact-schemas/README.md](./artifact-schemas/README.md) | **机器可读** JSON 字段规格 | [`multi_agent_code_factory/schemas/`](../../../multi_agent_code_factory/schemas/) |
| [artifact-templates/README.md](./artifact-templates/README.md) | **给人看** 的文档章节模板 | `multi_agent_code_factory/renderers/`（P0） |
| [examples/](./examples/README.md) | JSON / Mermaid **示例片段**（Todo 等） | — |
| [references/](./references/README.md) | 术语、MetaGPT、开源调研 | — |
| [quality-gates.md](./quality-gates.md) | **程序校验** rule_id、`validation` 配置 | `validators/`、`nodes/` |
| [implementation-plan.md](./implementation-plan.md) | **V1 编码计划**（阶段、PR 拆分、验收对照） | `multi_agent_code_factory/` |
| [python-style.md](./python-style.md) | **Python** 代码规范（PEP 8 / Ruff / pytest） | [`pyproject.toml`](../../../pyproject.toml) |

Schema 与人读模板细目见 [artifact-schemas/README.md](./artifact-schemas/README.md)、[artifact-templates/README.md](./artifact-templates/README.md)。

**Agent 角色命名：** [§3.1](./multi-agent-pipeline-design.md#31-角色命名约定)

**阅读顺序：** 主线 §1–§4、§6 → 本目录按需查表；**开始编码** → [implementation-plan.md](./implementation-plan.md)；抄 JSON 示例 → [examples/](./examples/README.md)。
