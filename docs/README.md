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

**V2 领域设计**（当前不实现）：[domains/](../domains/README.md)

## 易混淆对照

| 名称 | 设计 Spec（规格书） | Run 落盘（实例） |
|------|---------------------|------------------|
| Spec | `design/pipeline/artifact-schemas/spec.md` | `runs/<task_id>/spec.json` |
| 人读 PRD | `design/pipeline/artifact-templates/spec.md` | `runs/<task_id>/spec.md` |
| Python 规范 | `design/pipeline/python-style.md` | — |
