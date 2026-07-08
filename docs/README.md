# 文档目录

本仓库文档分 **三类**，避免与流水线 run 产物混淆：

| 路径 | 内容 | 谁写 | 示例 |
|------|------|------|------|
| **[`design/`](design/)** | **设计 Spec**（架构、产物规格、Profile） | 人 / 设计阶段 | `design/pipeline/multi-agent-pipeline-design.md` |
| **[`runs/`](runs/)** | **单次 run 审计产物** | PM / Architect / … Agent | `runs/todo-cli/spec.json` |
| （仓库外） | **生成业务代码** | Developer Agent | `../generated/default` |

## 设计 Spec 入口（V1）

| 文档 | 说明 |
|------|------|
| [design/00-master-overview.md](design/00-master-overview.md) | 项目总览与目标 |
| [design/pipeline/multi-agent-pipeline-design.md](design/pipeline/multi-agent-pipeline-design.md) | 多 Agent 流水线主线 |
| [design/pipeline/README.md](design/pipeline/README.md) | 工厂细目索引（Profile、产物规格、示例） |
| [design/pipeline/implementation-plan.md](design/pipeline/implementation-plan.md) | V1 实现计划（阶段、PR、验收） |
| [design/pipeline/P1-backlog.md](design/pipeline/P1-backlog.md) | **P1 待办汇总**（可勾选 checklist） |
| [operations.md](operations.md) | Live LLM、Ollama、VM 脚本与排错 |

**V2 领域设计**（当前不实现）：[domains/](../domains/README.md)

## 易混淆对照

| 名称 | 设计 Spec（规格书） | Run 落盘（实例） |
|------|---------------------|------------------|
| Spec JSON | `design/pipeline/artifact-schemas/prd-spec.md` | `runs/<task_id>/spec.json` |
| 人读 PRD | `design/pipeline/artifact-templates/prd-spec.md` | `runs/<task_id>/spec.md` |
| Design JSON | `design/pipeline/artifact-schemas/design-spec.md` | `runs/<task_id>/design.json` |
| 人读 Design | `design/pipeline/artifact-templates/design-spec.md` | `runs/<task_id>/design.md` |
| Mermaid 图 | `design/pipeline/artifact-templates/flow-spec.md` | `runs/<task_id>/*.mmd` |
| Review JSON | `design/pipeline/artifact-schemas/review-spec.md` | `runs/<task_id>/review.json` |
| 人读 Review | `design/pipeline/artifact-templates/review-spec.md` | `runs/<task_id>/review.md` |
| Python 规范 | `design/pipeline/python-style.md` | — |
