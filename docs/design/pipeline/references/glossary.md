# 术语表

## 依赖上游文档（只读）

本文 **非规范性** 术语速查；定义语境以总设计为准。


| 分类      | 上游文档                                                                      | 定位        |
| ------- | ------------------------------------------------------------------------- | --------- |
| **总设计** | [multi-agent-pipeline-design.md](../multi-agent-pipeline-design.md) | 系统的总体设计书 |
| **索引**  | [references/README.md](./README.md)                                       | 参考目录职责    |


---

> **主线：** [multi-agent-pipeline-design.md](../../pipeline/multi-agent-pipeline-design.md)

| 术语 | 含义 |
|------|------|
| **SOP** | Standard Operating Procedure；固定角色 + Schema 交接 |
| **Artifact** | 结构化 JSON 产物；配套 MD/Mermaid 为人读 |
| **HITL** | 人工审批；`prd_hitl` / `design_hitl` / `deploy_hitl` / `escalation_hitl` + `HitlDecision` |
| **再入点** | Agent 修订后主线第一站（如 PM→`prd_validate`、Developer→QA）；见主线 §4.3 |
| **escalation_hitl** | loop 触顶人工裁决（`on_limit_exceeded=escalation_hitl`）；≠ `deploy_hitl` |
| **Profile** | 领域配置：`code_root`（**仓库外**生成代码根）、`language`、`toolchain`、prompts、tools、hitl |
| **Run 目录** | `docs/runs/<task_id>/`；单次流水线 Artifact 与 `run_meta.json` |
| **设计 Spec** | `docs/design/`；人读架构文档，**非** Agent 运行时产物 |
| **Toolchain** | Profile 内构建/测试命令集（见 [profiles.md](../profiles.md)） |
| **Test Parser** | 将各语言测试输出归一化为 `TestReport` 的插件 |
| **Watch** | 节点执行前注入上下文的 Artifact 列表 |
| **RetryBundle** | Developer 重试时的 `test_report` + `failure_contexts` + `dev_manifest`（顶层 `prd`/`design` 由 `watch` 单独注入） |
| **Task-Batch** | 大项目首轮按 `dev_tasks` 分批实现；累积 `tasks_completed` / `changed_files` |
| **Reflexion** | 失败后结构化反思条目，纳入 RetryBundle |
| **ACI** | Agent-Computer Interface；Developer 侧窄 Tool 集（SWE-agent） |
| **ValidationReport** | `prd_validate` / `design_validate` 程序校验输出 |
| **产物校验** | PM/Architect 规则 + 可选 HITL |
| **Structured Output** | LLM 输出须符合 Pydantic schema |
| **以 X 为准** | 多份表述并存时，冲突与实现优先采纳的那一份（如配置以 YAML 为准、路由以代码为准） |
