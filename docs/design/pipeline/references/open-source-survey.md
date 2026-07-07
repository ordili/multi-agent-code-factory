# 其它开源与设计参考

> **原则：** 不替换 `multi_agent_code_factory` 主干（LangGraph + Profile + JSON Schema）。按 **模块** 从不同项目摘最佳实践。  
> **MetaGPT 开源态：** [main](https://github.com/FoundationAgents/MetaGPT/tree/main) 偏维护，**思想仍有效**；机制见 [metagpt.md](./metagpt.md)。  
> **主线：** [multi-agent-pipeline-design.md](../../pipeline/multi-agent-pipeline-design.md)

## C.1 重点借鉴一览（按优先级）

| 优先级 | 来源 | 借鉴什么 | 落点 | 阶段 |
|--------|------|----------|------|------|
| **P0** | [LangGraph](https://github.com/langchain-ai/langgraph) | checkpoint、**interrupt**（HITL）、条件边、`Command` 路由 | 主线 §4.6、§7 | P0–P1 |
| **P0** | [SWE-agent](https://github.com/SWE-agent/SWE-agent) | **极简 ACI**：少量专用 Tool | Developer `tools/` | P0 |
| **P0** | Reflexion（论文） | 失败后 **结构化反思** 写入 state | `DevManifest.reflection` | P0 |
| **P1** | [OpenHands](https://github.com/OpenHands/OpenHands) | **沙箱**内执行 shell/test | Profile.`sandbox` | P1 |
| **P1** | [Aider](https://github.com/Aider-AI/aider) | **Repo map**、git diff | Reviewer diff、§4.7 | P1 |
| **P1** | [CrewAI](https://github.com/crewAIInc/crewAI) | Role/Task 写进 **YAML** | Profile 格式 | P1 |
| **P2** | [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) | Handoff、guardrails、**MCP** | `tools/registry` | P2 |
| **P2** | [ChatDev](https://github.com/OpenBMB/ChatDev) | 阶段闸门 | 图节点边界（勿学群聊） | — |
| **P3** | AFlow | **工作流自优化** | `run_meta` 调 `loop_limits` | P3 |
| **不借鉴** | AutoGen GroupChat | 自由多轮对话 | — | 与反幻觉目标冲突 |

## C.2 分项目摘要

### LangGraph（编排层，已选型）

| 值得借鉴 | 不必照搬 |
|----------|----------|
| checkpointer、`interrupt_before` deploy_hitl | Studio 替代自有 `run` 目录 |
| 子图：Developer→QA→Reviewer | 单一大图塞全部逻辑 |

### OpenHands（沙箱）

Docker 内跑 `test_command`；Profile 增 `sandbox: docker | local`（默认 local）。

### SWE-agent（Developer Tool）

窄接口：`read_file`、`write_file`、`run_shell`（受限）、`linter`；禁止 open-ended shell。

### Aider（增量改码）

Reviewer Tool `git_diff(code_root)`；§4.7 增量 run 读 `parent_task_id`。

### CrewAI（Profile）

`profiles/<id>/agents.yaml` 定义五角色 prompt；`graph.py` 不变。

### ReAct + Reflexion

`DevManifest.reflection` 示例：

```json
"reflection": { "attempt": 2, "hypothesis": "...", "next_action": "..." }
```

纳入 RetryBundle，Pydantic 校验。

## C.3 能力拼图

```text
  文档/SOP          执行/沙箱         编排/HITL
  MetaGPT           OpenHands         LangGraph
  CrewAI            SWE-agent         LangSmith
  ChatDev(阶段)     Aider(diff)
        \               |               /
         v             v             v
              multi_agent_code_factory（本设计）
         Profile · JSON · watch · 三层回路
```

## C.4 纳入设计的扩展项

| 扩展 | Schema / 配置 | 阶段 |
|------|----------------|------|
| `DevManifest.reflection` | [dev-manifest.md](../artifact-schemas/dev-manifest.md) | P0 |
| `Profile.toolchain` + `test_parsers/` | [profiles.md](../profiles.md)、[test-report.md](../artifact-schemas/test-report.md) | P0 |
| `Profile.sandbox` | [profiles.md](../profiles.md) | P1 |
| Parser：`go_json` / `cargo_json` / `forge_json` | [profiles.md §3](../profiles.md#3-profile-矩阵) | P1 |
| `Profile.agents.yaml` | [profiles.md](../profiles.md) | P1 |
| Reviewer Tool `git_diff` | 主线 §4.2 | P1 |
| `Profile.mcp_servers` | [profiles.md](../profiles.md) | P2 |

## C.5 实现 backlog

```text
P0  watch/RetryBundle + spec_validate/design_validate + Developer Tool 收敛 + reflection + test_parsers（junit_xml）
P1  Profile.sandbox + go_json/cargo_json/forge_json + git_diff + agents.yaml
P2  MCP 注册
P3  AFlow 式工作流调参（离线分析 run_meta）
```

与 **[metagpt.md §B.3](./metagpt.md#b3-实现-backlog设计已定待编码)** 合并排期。

## C.6 与 metagpt.md 的分工

| 文档 | 范围 |
|------|------|
| **[metagpt.md](./metagpt.md)** | MetaGPT：SOP、结构化产物、watch、executable feedback |
| **本文** | 其它：沙箱、ACI、diff、Profile 组织、MCP、论文模式 |
