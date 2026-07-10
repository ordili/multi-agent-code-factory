# 产物续跑（Artifact Continue）— 设计说明

> **日期：** 2026-07-10  
> **状态：** 已定稿（经二轮审查修订）  
> **关联规范：** [multi-agent-pipeline-design.md §4.3 / §4.6](../../design/pipeline/multi-agent-pipeline-design.md)、[run-meta-spec.md](../../design/pipeline/artifact-schemas/run-meta-spec.md)、[P1-backlog.md §4](../../design/pipeline/P1-backlog.md)

---

## 需求说明

当前 `python -m multi_agent_code_factory run --task-id <id>` 每次从 PM 重头执行，无法利用 `docs/runs/<task_id>/` 下已有产物继续推进。实际运行中常见以下中断/失败场景，需要**根据磁盘上已有文档与代码**续跑，而不是全流水线重来：

1. **设计文档已生成，规则校验未通过**  
   下次执行应：先对现有 `design.json` / `design.md` 做 **design_validate**（不调 LLM）；若仍失败，再调 Architect 模型根据 violations 修订；通过后进入 Developer。

2. **需求文档已生成，规则校验未通过**  
   同上，再入点为 **spec_validate**；失败则调 PM 修订。

3. **代码已生成，测试失败（含 `tests_missing` 门禁）**  
   下次执行应：先在 **QA** 对 `code_root` 重跑测试（不调 LLM）；若仍失败，将 `test_report`（failures / `tests_missing`）交给 Developer 调 LLM 修代码；修完再回 QA。符合主线 §4.3 实现环再入规则。

4. **LLM 调用次数或重试次数触顶导致 `status=failed`**  
   例如 `impl_retry_count` 达到 `max_impl_retries`，或 `budget.used_llm_calls` 已达上限。续跑时应**重置用量计数**（`used_llm_calls` / `used_tokens` 归零），并重置已触顶的回路计数器（如 `impl_retry_count`），否则一进入图就会再次 fail。

5. **统一原则：先门禁、后模型**  
   续跑第一步**优先**执行规则校验或测试（无 LLM 成本）；门禁未通过再调对应 Agent 的 LLM。若人工已修改产物/代码使门禁通过，应能零 LLM 调用进入下游。  
   **例外：** spec 已通过且尚无 `design.json` 时，再入点为 `architect`，第一步生成 design（无门禁可跑）。详见 [§图执行](#图执行门禁先跑再-invoke)。

6. **`run` 与续跑语义分离**  
   同一 `task_id` 已有 run 目录时，不应默认覆盖重跑；应提供专用续跑命令，避免误清空进度。

本方案只描述**一种实现路径**：**产物续跑（`continue`）**，复用现有 LangGraph 节点与路由，不另起一套流水线。

---

## 方案概述

新增 CLI 子命令 **`continue`**：水合 `PipelineState` → 推断再入点 → **先显式执行门禁**（若有）→ `update_state` + `invoke`，后续走现有 `route_after_*` 与 Agent。

```text
continue --task-id X
  → 加载 JSON 产物 + run_meta（跳过 stale，见 §产物水合）
  → load_profile(id)，覆盖 code_root（见 §Profile 与 Context 重建）
  → 重置 budget；触顶回路计数归零（见 §续跑时的重置策略）
  → 推断再入点
  → 有门禁：显式 run_* → update_state(as_node=门禁) → invoke
  → 无门禁（architect）：update_state(as_node=route_after_spec_validate) → invoke
  → route_after_* → Agent（按需 LLM）→ …
```

| 命令 | 用途 |
|------|------|
| **`continue`** | 按磁盘产物续跑（本方案，V1 首选） |
| **`resume`**（后续） | 进程崩溃 / HITL interrupt 后从 `checkpoint.db` 恢复 |

二者可共用 SqliteSaver；**`continue` 不依赖**历史 checkpoint 内容（P1 初版可走产物推断，`resume` 见 §范围说明）。

---

## 再入点与执行顺序

与 [§4.3 再入规则](../../design/pipeline/multi-agent-pipeline-design.md#43-循环路由hitl-与-deploy) 对齐。推断取「**当前阻塞失败最下游、产物齐全**」的门禁：

| 磁盘 / 元数据状态 | 再入点 | 门禁未过后调用的 Agent |
|-------------------|--------|-------------------------|
| `spec_validation.passed = false` | `spec_validate` | PM |
| `design_validation.passed = false` | `design_validate` | Architect |
| `test_report` 失败 / `tests_missing` / `impl_retry` 触顶且 `failed` | `qa` | Developer |
| Reviewer `next_stage = architect` | `design_validate` | Architect |
| Reviewer `next_stage = developer` | `qa` | Developer |
| Reviewer `next_stage = pm` | `spec_validate` | PM |
| spec 已通过、无 `design.json` | `architect` | —（第一步即 LLM） |

**Developer 反馈衔接：** 触顶续跑时 `impl_retry_count` 先归零；QA 失败后 `route_after_qa` 置为 `1` 再进 Developer，`format_qa_retry_feedback` 可注入最新 `test_report`。

---

## 续跑时的重置策略

| 字段 | 默认行为 | 原因 |
|------|----------|------|
| `budget.used_llm_calls` / `used_tokens` | → `0`（**始终**，不受 `--no-reset-loops` 影响） | 新 session 重新计 LLM 用量 |
| `impl_retry_count` | `failed` 且已达 `max_impl_retries` → `0` | 否则 `route_after_qa` 立即触顶 |
| `design_revision_count` | `failed` 且已达 `max_design_revisions` 且 design 仍失败 → `0` | 同上 |
| `spec_revision_count` | `failed` 且已达 `max_spec_revisions` 且 spec 仍失败 → `0` | 同上 |
| `status` / `finished_at` | → `running` / `null` | |

**不重置：** `loop_limits.*`、`profile` 快照、`code_root` 源码、未触顶的回路计数、`llm_usage.json` 历史（仅追加 `event=continue` 审计条目）。

`--no-reset-loops`：仅保留触顶回路计数，**不**影响 budget 重置。

---

## CLI 约定

```bash
python -m multi_agent_code_factory continue --task-id calculator-10-01 --live
python -m multi_agent_code_factory continue --task-id X --reenter qa --live
python -m multi_agent_code_factory continue --task-id X --no-reset-loops

python -m multi_agent_code_factory run --task-id X "用户需求..."
python -m multi_agent_code_factory run --task-id X --force-new "..."
```

| 命令 | 行为 |
|------|------|
| `run` + 已存在 run 目录 | **默认拒绝** → 用 `continue` 或 `--force-new` |
| `continue` | 水合、重置、先门禁后 invoke；无需再传 `user_request` |
| `continue` + `status=completed` | **拒绝** |

`code_root` 默认取自 `run_meta` 快照；对曾 `--live` 的 run 用 `--stub` 续跑应 **warning** 或要求 `--live`。

---

## 产物水合（Hydrate）

模块：`multi_agent_code_factory/tools/run_artifacts/loader.py`。

| 来源 | 映射到 state |
|------|----------------|
| `run_meta.json` | `task_id`、`*_count` |
| `run_meta.user_request` | `user_request`（缺失时从 `spec` 降级，打 warning） |
| `spec.json` | `spec` |
| `spec_validation.json` | `spec_validation` |
| `design.json` | `design` |
| `design_validation.json` | `design_validation` |
| `dev_manifest.json` | `dev_manifest` |
| `test_report.json` | `test_report` |
| `review.json` | `review` |
| `hitl.json` | `hitl` |

### stale 产物

`run_meta.stale_artifacts[]` 中的文件**不载入、不参与推断**（文件可留盘审计）。依赖产物仅存在 stale 版本时，按「产物缺失」报错。

首次 `run` 须写入 `run_meta.user_request`。水合后 state 须满足再入点前置条件（如 `qa` 需 `design` + `dev_manifest`）。

---

## Profile 与 Context 重建

`run_meta.profile` 快照仅含 `id`、`language`、`code_root`、`toolchain`。续跑时：

1. `load_profile(run_meta.profile.id)` 加载完整 `ProfileConfig`
2. 快照 / CLI `--code-root` 覆盖 `code_root`
3. `LoopLimits` 从 `run_meta.loop_limits` 反序列化
4. 新建 `RunArtifactWriter`、`LlmRunner`（读重置后 `budget`）

`PipelineRunContext` 不进 checkpoint，每次 `continue` 重建。

---

## 图执行：门禁先跑，再 invoke

`START → pm` 为常态入口。LangGraph `update_state(as_node=X)` 表示 X **已执行完**，`invoke` 从 X 的**后继**开始，**不会重跑 X**。

```python
app = build_graph(checkpointer=SqliteSaver(run_dir / "checkpoint.db"))
config = {"configurable": {"thread_id": task_id}}
state = hydrate_state(run_dir, run_meta)
ctx = rebuild_context(run_meta, ...)

if reentry in ("spec_validate", "design_validate", "qa"):
    patch = run_gate(reentry, state, ctx)  # run_spec_validate / run_design_validate / run_qa
    state = merge(state, patch)
    app.update_state(config, state, as_node=reentry)
elif reentry == "architect":
    # spec 已通过，无 design；跳过门禁，从 route 进 architect
    state.pipeline_route = "architect"
    app.update_state(config, state, as_node="route_after_spec_validate")
app.invoke(None, config=config, context=ctx)
```

| 再入点 | 续跑第一步 | `update_state(as_node=…)` 后 invoke 进入 |
|--------|------------|------------------------------------------|
| `spec_validate` | `run_spec_validate` | `route_after_spec_validate` |
| `design_validate` | `run_design_validate` | `route_after_design_validate` |
| `qa` | `run_qa` | `route_after_qa` |
| `architect` | 无（水合 spec + spec_validation.passed=true） | `architect` → `design_validate` → … |

**依赖：** `langgraph-checkpoint-sqlite`；`PipelineState` 自定义 serde（Pydantic `model_dump` / `model_validate`）+ round-trip 单测。

---

## 再入点自动推断

输入：`run_dir`、`run_meta`、`stale_artifacts` 过滤后的磁盘 JSON。优先级：

1. `review.json` 非 stale 且 `next_stage` ∈ `{pm, architect, developer}` → `spec_validate` / `design_validate` / `qa`
2. `spec_validation` 非 stale 且 `passed=false` → `spec_validate`
3. `design_validation` 非 stale 且 `passed=false` → `design_validate`
4. `test_report` 非 stale 且（`passed=false` 或 `tests_missing` 非空），**或**（`impl_retry` 触顶 + `status=failed` + 有效 `dev_manifest`）→ `qa`
5. 有有效 `design.json`、无有效（非 stale）`dev_manifest` → `design_validate`
6. `spec` 已校验通过且无 `design.json` → `architect`
7. 无法推断 → 报错，建议 `--reenter`

`--reenter` 跳过推断，仍校验前置条件。`status=running` 且存在未完成 `checkpoint.db` 时，P1 仍走上述推断；`resume` 优化见 §范围说明。

---

## 运行时边界

| 场景 | 行为 |
|------|------|
| `status=completed` | 拒绝 `continue` |
| `status=failed` + 触顶 | 重置触顶计数 + budget，按 §再入点推断 |
| 人工已修复代码/产物 | 门禁通过 → 零 LLM 进下游 |
| stale 与当前产物并存 | 仅非 stale 推断/水合 |
| `continue --stub` 对曾 `--live` 的 run | warning 或要求 `--live` |

---

## 示例：`calculator-10-01`

- `design_validation` 已通过；`dev_manifest` 存在；`impl_retry_count=3` 触顶；`status=failed`
- `test_report.json` 在 `stale_artifacts` 中 → 不水合；推断走规则 4（触顶 + `dev_manifest`）→ **`qa`**

```bash
python -m multi_agent_code_factory continue --task-id calculator-10-01 --live
```

预期：重置 `used_llm_calls`、`impl_retry_count` → 显式 `run_qa` → `route_after_qa` → 失败则 Developer（`impl_retry_count=1`）→ 不重跑 PM/Architect。

---

## 实现落点

| 模块 | 变更 |
|------|------|
| `pyproject.toml` | `langgraph-checkpoint-sqlite` |
| `__main__.py` | `continue` 子命令；`run` 防覆盖 |
| `graph/runner.py` | `continue_pipeline()` |
| `tools/run_artifacts/loader.py` | 水合 + stale 过滤 |
| `tools/run_artifacts/meta.py` | `user_request`；`prepare_continue()` |
| `checkpoint.py` | SqliteSaver、`infer_reentry_node()`、serde |
| `graph/graph_builder.py` | `build_graph(checkpointer=...)` |
| `schemas/run_meta.py` | `user_request` |
| `tests/` | serde、推断、stub 集成（design 失败 / QA 失败续跑） |

实施顺序：`user_request` + loader → 推断 + `prepare_continue` → serde + 门禁 + `update_state` 集成 → live 验证 `calculator-10-01` → README。

---

## 范围说明（Out of scope）

| 包含 | 不包含 |
|------|--------|
| 产物续跑、先门禁后 LLM、预算/触顶重置、`continue`、stale 过滤 | HITL interrupt UI（P1 另项） |
| | `--parent-task-id` 增量（P2） |
| | **`resume` 崩溃恢复**（后续叠加，共用 SqliteSaver） |

---

## 验收标准

- [ ] design 校验失败：`design_validate` → Architect，不重跑 PM（§需求 1）
- [ ] 测试失败：`run_qa` → Developer + `test_report`，不重跑 PM/Architect（§需求 3）
- [ ] 触顶续跑：budget + `impl_retry_count` 重置后可再进 Developer（§需求 4）
- [ ] 人工修复后门禁通过：零 LLM 进下游（§需求 5）
- [ ] stale 不参与水合/推断；`completed` 拒绝 `continue`；`run` 防覆盖（§产物水合、§CLI）
- [ ] `architect` 再入：无 design 时第一步 LLM，再 `design_validate`（§图执行）
- [ ] `load_profile(id)` + 快照 `code_root`；`llm_usage.json` 追加 `continue` 事件

---

## 与主线文档的同步

- `multi-agent-pipeline-design.md` §4.6：`continue` vs `resume`
- `P1-backlog.md` §4
- `README.md`：`continue` 示例
