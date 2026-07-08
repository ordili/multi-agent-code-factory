# MetaGPT 借鉴清单

> **参考：** [MetaGPT 论文](https://arxiv.org/html/2308.00352v7) · [GitHub](https://github.com/FoundationAgents/MetaGPT)  
> **原则：** 不替换本项目的 LangGraph 流水线；吸收 SOP、结构化交接、executable feedback 等可验证机制。  
> **主线：** [multi-agent-pipeline-design.md](../../pipeline/multi-agent-pipeline-design.md)

## B.1 MetaGPT 核心公式

```text
Code = SOP(Team)
```

用人类软件公司的 **标准作业程序（SOP）+ 角色专精 + 结构化交接** 替代 Agent 自由群聊，降低幻觉与级联错误。

| 支柱 | MetaGPT 做法 |
|------|----------------|
| **SOP 装配线** | PM → Architect → PM 分任务 → Engineer → QA |
| **结构化交接** | PRD、设计文档、类图、序列图（非闲聊） |
| **消息池 + 订阅** | 全局 Message Pool；各角色 `watch` 前置产物后行动 |
| **Executable Feedback** | Engineer 跑测试/执行，对照 PRD + 设计自修，约 3 轮 |

## B.2 已借鉴（本设计已覆盖）

| MetaGPT | 本流水线 | 落点 |
|---------|----------|------|
| 角色专精 | PM / Architect / Developer / QA / Reviewer | 主线 §3、§4.2 |
| SOP 有序主线 | LangGraph 顺序图 + 条件回路 | 主线 §4.1 |
| 结构化产物 | JSON Schema + MD + Mermaid | 主线 §2、[artifact-schemas/](../artifact-schemas/README.md) |
| PRD → 设计 → 代码 | `spec` → `design` → Profile.`code_root` | [profiles.md](../profiles.md) |
| Architect 交付物 | 文件列表、接口、序列图、`dev_tasks` | [artifact-schemas/design-spec.md](../artifact-schemas/design-spec.md) |
| Executable feedback | `run_tests` Tool + Parser + RetryBundle | 主线 §4.5.1、[test-report.md](../artifact-schemas/test-report-spec.md) |
| **Watch / 订阅** | 消息池 + `watch` | `context.py`（主线 §4.5） |
| **PM 产物** | KPI、Features、User Stories、Requirement Pool | [artifact-schemas/prd-spec.md](../artifact-schemas/prd-spec.md) |
| **设计文档模板** | Google Design Doc + 七项工程 | [artifact-templates/design-spec.md](../artifact-templates/design-spec.md) |
| **断点恢复** | `recover_path` | checkpoint（主线 §4.6） |
| **运行预算** | `investment` | `budget` / `run_meta`（主线 §4.4） |
| **增量开发** | PlanAndChange | `parent_task_id`、`revision`（主线 §4.7） |
| 重试上限 | ~3 轮 Engineer 自修 | `loop_limits`（主线 §4.4） |
| 产物落盘 | Profile.`code_root`（仓库外）+ `docs/runs/` | 主线 §6.1 |

## B.3 实现 backlog（设计已定，待编码）

> **排期与 PR 拆分：** [implementation-plan.md](../implementation-plan.md)

| 项 | 落点 | 阶段 |
|----|------|------|
| `context.py`：按 `watch` 组装 `NodeContext` | 主线 §4.5 | P0 |
| RetryBundle + 失败文件片段 Tool | 主线 §4.5.1 | P0 |
| Developer Tool 收敛（SWE-agent ACI，[open-source-survey.md](./open-source-survey.md)） | 主线 §4.2 | P0 |
| `DevManifest.reflection`（Reflexion） | [dev-manifest.md](../artifact-schemas/dev-manifest-spec.md) | P0 |
| 各角色 prompt 显式列出 `watch` 字段 | 主线 §4.5 | P0 |
| `spec_validate` / `design_validate` + `validators/` | [quality-gates.md](../quality-gates.md) | P0 |
| `spec_hitl` / `design_hitl` | 主线 §4.1.2 | P1 |
| `toolchain` 配置与 Profile 快照 | [profiles.md](../profiles.md) | P0 |
| `go_json` / `cargo_json` / `forge_json` Parser | [profiles.md §3](../profiles.md#3-profile-矩阵) | P1 |
| LangGraph checkpointer + `resume` CLI | 主线 §4.6 | P1 |
| `Profile.sandbox`（OpenHands） | [profiles.md](../profiles.md) | P1 |
| Reviewer `git_diff` Tool（Aider） | [open-source-survey.md](./open-source-survey.md) | P1 |
| `profiles/*/agents.yaml`（CrewAI 风格） | [profiles.md](../profiles.md) | P1 |
| QA `tests_missing` 检测；`auto_generate_tests` | [test-report.md](../artifact-schemas/test-report-spec.md) | P1 |
| `--parent-task-id` 增量 merge | 主线 §4.7 | P2 |
| `budget` 触顶熔断 | 主线 §4.4 | P2 |
| `Profile.mcp_servers` | [open-source-survey.md](./open-source-survey.md) | P2 |

## B.4 刻意不同（不必向 MetaGPT 回退）

| 维度 | MetaGPT | 本流水线 | 原因 |
|------|---------|----------|------|
| **编排** | Team + 消息池（偏动态） | LangGraph 条件图 | 路由可验证、Trace 清晰 |
| **设计返工** | 无自动回 Architect | `next_stage=architect` / `pm` | 真实研发常见架构/需求返工 |
| **测试** | 部分依赖 LLM 审查 | `run_tests` + Parser → `TestReport` | 避免编造「测试通过」 |
| **审查** | 审查易幻觉 | 独立 Reviewer + `acceptance_coverage` | 对齐 PM 验收项 |
| **生产变更 HITL** | 无 | Profile.`hitl` + `design.hitl_flags` | 领域相关审批可配置 |
| **回路上限** | 硬编码约 3 轮 | `loop_limits` 可配置 | 运维可调 |
| **节点交接** | 以 MD / Message 为主 | **以 JSON Schema 为准** | 程序解析与路由 |

## B.5 暂不需要借鉴

| MetaGPT 能力 | 原因 |
|--------------|------|
| 多 Engineer 并行（`n_borg`） | 代码库规模小，单 Developer 足够 |
| TeamLeader 自由群聊 | 与「减少幻觉」目标相反 |
| 竞品象限图、UI 设计 | 非通用工厂 MVP |
| 自改 constraint prompt | 复杂度高，后续再评估 |
| 直接作为 PROD 运行时 | 工厂只负责**生成代码** |

## B.6 实现阶段对照

```text
P0  context.py（watch + RetryBundle）· 角色 prompt 订阅清单
P1  checkpoint/resume · Test tests_missing 检测
P2  增量 --parent-task-id · budget 熔断
```

## B.7 与主线 §4.1.1 的关系

主线 [§4.1.1 MetaGPT 对比摘要](../multi-agent-pipeline-design.md#411-与-metagpt-对比摘要) 为流程级差异；**本文** = MetaGPT 机制与 backlog；**[open-source-survey.md](./open-source-survey.md)** = 其它开源项。
