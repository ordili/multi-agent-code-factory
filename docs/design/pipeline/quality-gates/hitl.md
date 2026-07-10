# HITL 节点与 Reviewer 分工

## 依赖上游文档（只读）

审查 / 修订本文时 **仅以本表及正文流程约定为准**；不引用节点实现代码。


| 分类        | 上游文档                                                                                  | 定位                              |
| --------- | ------------------------------------------------------------------------------------- | ------------------------------- |
| **总设计**   | [multi-agent-pipeline-design.md](../multi-agent-pipeline-design.md) | 系统的总体设计书 |
| **JSON 契约** | [hitl-spec.md](../artifact-schemas/hitl-spec.md)                                      | Run `hitl.json` 字段              |
| **门禁索引**  | [README.md](./README.md)                                                              | Profile `hitl` / `require_hitl` |
| **规则**    | [spec-validate.md](./spec-validate.md)                                                | spec 校验通过后的 HITL 路由前提           |
| **规则**    | [design-validate.md](./design-validate.md)                                            | design 校验通过后的 HITL 路由前提         |


---

> **索引：** [quality-gates/README.md](./README.md)  
> **Schema：** [hitl-spec.md](../artifact-schemas/hitl-spec.md)  
> **规则清单：** [spec-validate.md](./spec-validate.md) · [design-validate.md](./design-validate.md)（HITL 无独立 `rule_id`，仅路由与 Profile 配置）

---

## 5. HITL 节点（spec_hitl / design_hitl / deploy_hitl / escalation_hitl）

LangGraph **`interrupt_before`**；[`HitlDecision.stage`](../artifact-schemas/hitl-spec.md)：

| `stage` | 节点 | 审批人阅读 | 驳回 / 终止 |
|---------|------|------------|-------------|
| `spec` | spec_hitl | `spec.md`、`spec_validation.json` | → PM |
| `design` | design_hitl | `design.md`、`*.mmd`、`design_validation.json` | → Architect |
| `deploy` | deploy_hitl | `review.md`、diff、敏感变更 | 续跑 → Developer；终止 → `run_meta.status=failed` |
| `escalation` | escalation_hitl | run 摘要、回路计数、最近失败产物 | → `run_meta.status=failed` |

### 5.1 escalation_hitl（loop 触顶，P1）

**配置：** `on_limit_exceeded: escalation_hitl`（默认 `fail`，MVP 可不实现节点）。

| 项 | 约定 |
|----|------|
| **触发** | 任一回路的 `*_revision_count` 或 `impl_retry_count` 达 `loop_limits` 上限 |
| **写入** | `hitl.json`（`stage=escalation`）；`reason` 示例：`loop_limit:impl_retry`、`loop_limit:spec_revision` |
| **继续** | `approved=true` 且人工在 CLI/UI 指定重置计数 → 从主线 [§4.3 再入点](../multi-agent-pipeline-design.md#再入规则升环--validate-失败后) 续跑 |
| **与 deploy_hitl** | **不可互换**；deploy 仅 Reviewer 成功路径 + Profile.`hitl` 敏感规则 |

---

## 6. 与 Reviewer Agent 的分工

| | spec_validate / design_validate | Reviewer（LLM） |
|--|--------------------------------|-----------------|
| **时机** | Developer 前 | QA 后 |
| **对象** | 文档规则 | 代码 + 测试 + AC |
| **确定性** | 是 | 否 |

规则清单分别见 [spec-validate.md](./spec-validate.md)、[design-validate.md](./design-validate.md)。
