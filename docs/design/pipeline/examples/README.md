# 工厂 — JSON / 图 示例

> **字段规格以：** [../artifact-schemas/](../artifact-schemas/README.md) **为准**  
> **人读模板与长样例：** [../artifact-templates/](../artifact-templates/README.md)  
> **主线：** [multi-agent-pipeline-design.md](../../pipeline/multi-agent-pipeline-design.md) §5 索引

本目录存放 **可拷贝的示例片段**；完整嵌套类型与校验规则以 `artifact-schemas/` 为准。

## 目录

| 路径 | 说明 |
|------|------|
| [snippets/spec-default.json](./snippets/spec-default.json) | Profile=`default` 的 `SpecArtifact` 节选 |
| [snippets/spec-context-rust.json](./snippets/spec-context-rust.json) | Rust `spec.context` + AC 节选 |
| [snippets/spec-context-solidity.json](./snippets/spec-context-solidity.json) | Solidity `spec.context` + AC 节选 |
| [snippets/design-todo-excerpt.json](./snippets/design-todo-excerpt.json) | Todo `DesignArtifact` 节选（完整见 [design-spec.md](../artifact-schemas/design-spec.md)） |
| [snippets/flow-todo.mmd](./snippets/flow-todo.mmd) | Todo 时序图节选 |
| [snippets/pipeline-overview.mmd](./snippets/pipeline-overview.mmd) | **全线流程图**（产物 + 条件回路 + **再入点** + escalation；§1 / §4.1） |

## Run 落盘

单次 run 的完整产物路径：`docs/runs/<task_id>/`（见主线 §6.1）。
