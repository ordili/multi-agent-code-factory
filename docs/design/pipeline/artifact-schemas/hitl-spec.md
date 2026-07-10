# hitl-spec.md — HitlDecision（HITL JSON 契约）

## 依赖上游文档（只读）

审查 / 修订本文时 **仅以本表及正文字段定义为准**。`quality-gates/hitl.md` 为**下游**，不在此表列出。


| 分类      | 上游文档                                                                          | 定位                            |
| ------- | ----------------------------------------------------------------------------- | ----------------------------- |
| **总设计** | [multi-agent-pipeline-design.md](../multi-agent-pipeline-design.md) | 系统的总体设计书 |
| **运行配置** | [profiles.md](../profiles.md)                                               | `hitl`、`require_hitl` 等 Profile 字段 |


---

> **实现：** `multi_agent_code_factory/schemas/hitl.py`  
> **Run 路径：** `hitl.json`  
> **节点：** `spec_hitl`、`design_hitl`、`deploy_hitl`、`escalation_hitl`

## 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | `"1"` | |
| `stage` | enum | `spec` \| `design` \| `deploy` \| `escalation`（loop 触顶，`escalation_hitl` 节点） |
| `required` | boolean | 本 stage 是否须经人工 |
| `reason` | string[] | 如 `validation.spec.require_hitl`、`hitl_flag:touches_production` |
| `approved` | boolean? | 人工填写 |
| `reviewer` | string? | 审批人 |
| `comment` | string? | 驳回/批准说明 |

**多轮 HITL：** 当前 interrupt 写入 `hitl.json`；每次决议追加到 `run_meta.hitl_history[]`（或 `hitl_log.jsonl`，P1）。`stage` 区分同文件内的最后一次待决记录。

## 各 stage 对照

| `stage` | 节点 | 审批人阅读 | 驳回回到 |
|---------|------|------------|----------|
| `spec` | spec_hitl | `spec.md`、`spec_validation.json` | PM |
| `design` | design_hitl | `design.md`、`flow.mmd`、`design_validation.json` | Architect |
| `deploy` | deploy_hitl | `review.md`、diff、敏感变更 | 续跑 → Developer（再入 QA）；终止 → `run_meta.status=failed` |
| `escalation` | escalation_hitl | run 摘要、`loop_limits` 计数 | 终止 run / 重置计数后继续（P1） |

`reason` 取值示例：`validation.spec.require_hitl`、`hitl_flag:touches_production`、`loop_limit:impl_retry`。Profile 中 `validation` / `hitl` 配置见 [profiles.md](../profiles.md) 与主线 [§4.1.2](../multi-agent-pipeline-design.md#412-产物校验与-hitlpm--architect)。

## 示例（design 阶段）

```json
{
  "version": "1",
  "stage": "design",
  "required": true,
  "reason": ["validation.design.require_hitl", "hitl_flag:touches_production"],
  "approved": true,
  "reviewer": "gidon",
  "comment": "模块划分与 AC 覆盖 OK"
}
```

## 示例（escalation 阶段，P1）

```json
{
  "version": "1",
  "stage": "escalation",
  "required": true,
  "reason": ["loop_limit:impl_retry", "impl_retry_count:3"],
  "approved": null,
  "reviewer": null,
  "comment": null
}
```
