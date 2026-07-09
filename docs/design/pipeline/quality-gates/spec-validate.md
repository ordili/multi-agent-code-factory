# spec_validate — 规则清单

> **索引：** [quality-gates/README.md](./README.md)  
> **实现：** `multi_agent_code_factory/validators/spec_rules.py` · `spec_md_rules.py`  
> **JSON 契约：** [artifact-schemas/prd-spec.md](../artifact-schemas/prd-spec.md)  
> **人读模板：** [artifact-templates/prd-spec.md](../artifact-templates/prd-spec.md) → Run `spec.md`

**rule_id 合计：** **44** 条（§3.1 结构 **15** · §3.2 可测性 **16** · §3.3 `spec.md` 格式 **13**）。

---

## 3.1 结构与必填

本节 `severity` 均为 **error**。

| rule_id | 严重度 | 必检 | 触发条件 | 字段 | 判定 |
|---------|--------|------|----------|------|------|
| `SPEC-001` | error | 是 | — | `acceptance_criteria` | 非空 |
| `SPEC-002` | error | 是 | — | `acceptance_criteria[].id` | 唯一 |
| `SPEC-003` | error | 是 | — | `scope_in` | 非空 |
| `SPEC-004` | error | 是 | — | `title`、`summary` | 非空 |
| `SPEC-005` | error | 是 | — | `profile` | 与 CLI Profile 一致 |
| `SPEC-006` | error | 条件 | Profile 配置 `language` | `context.language` | 与 Profile.`language` 一致 |
| `SPEC-007` | error | 条件 | Profile 配置 `context_schema` | `context` | 通过 `context_schema`（const / enum） |
| `SPEC-008` | error | 是 | — | `user_stories[].id` / `requirement_pool[].id` / `features[].id` / `success_metrics[].id` | 各类内无重复 |
| `SPEC-009` | error | 是 | — | `features` | 非空 |
| `SPEC-010` | error | 是 | — | `features[].id` | 唯一 |
| `SPEC-012` | error | 条件 | `success_metrics` 非空 | `success_metrics[].id`、`success_metrics[].target` | id 唯一；`target` 非空 |
| `SPEC-013` | error | 是 | — | `operational_profile` | 对象须存在 |
| `SPEC-014` | error | 是 | — | `operational_profile.user_scale`、`high_concurrency`、`performance.tier` | 必填 |
| `SPEC-015` | error | 是 | — | `consistency_profile` | 对象须存在 |
| `SPEC-016` | error | 是 | — | `consistency_profile.consistency_model`、`delivery`、`multi_writer`、`idempotency_required` | 必填 |

> **必检：** **是** = 每次 `spec_validate` 均执行；**条件** = 仅当触发条件成立时执行。  
> **字段** 列与 [prd-spec.md](../artifact-schemas/prd-spec.md) JSON 契约一致（英文键名）。  
> **`success_metrics`（非 rule_id）：** 可选；JSON 可为 `[]`，无 empty 门禁。

## 3.2 可测性与一致性

| rule_id | 严重度 | 必检 | 触发条件 | 字段 | 判定 |
|---------|--------|------|----------|------|------|
| `SPEC-101` | error | 是 | — | `acceptance_criteria[].description` | 非空 |
| `SPEC-102` | warn | 是 | — | `acceptance_criteria[].verifiable_by` | P0 覆盖（文档；实现待对齐） |
| `SPEC-103` | warn | 是 | — | `scope_out` | 与 `scope_in` 互斥 |
| `SPEC-104` | warn | 条件 | `constraints` 非空 | `constraints[]` | 条目非空 |
| `SPEC-105` | error | 是 | — | `requirement_pool[].feature_id` | 引用合法 `features[].id` |
| `SPEC-106` | warn | 是 | — | `features[]`（P0） | 在 AC 或 KPI 中可追溯 |
| `SPEC-107` | warn | 是 | — | `requirement_pool[]`、`features[]` | 描述不得逐条重复 |
| `SPEC-108` | warn | 条件 | `high_concurrency=true` | `operational_profile.performance.tier` | 不应为 `best_effort` |
| `SPEC-109` | warn | 条件 | `performance.tier=custom` | `operational_profile.performance.notes` | 非空 |
| `SPEC-110` | warn | 条件 | `consistency_model=eventual` | `consistency_profile.notes` | 宜含定性滞后预期 |
| `SPEC-111` | error | 条件 | `consistency_model=custom` | `consistency_profile.notes` | 非空 |
| `SPEC-112` | warn | 条件 | `multi_writer=true` | `consistency_profile.conflict_strategy` | 不应为 `not_applicable` |
| `SPEC-113` | warn | 条件 | `idempotency_required=true` 且 `delivery=at_least_once` | `acceptance_criteria` / `success_metrics` | 宜覆盖重试/幂等 |
| `SPEC-114` | warn | 是 | — | `operational_profile`、`consistency_profile` 数值子字段 | `latency` 等宜为空（数值归属 design） |
| `SPEC-201` | warn | 是 | — | `acceptance_criteria[].verifiable_by` | 宜含 `automated_test` |
| `SPEC-202` | warn | 是 | — | `revision` | ≥ 1 |

## 3.3 Run `spec.md` 格式（P1，warn）

本节 `severity` 均为 **warn**。

校验 Run 目录 **`spec.md`**（非规范文件名 `prd-spec.md`）。章节模板见 [artifact-templates/prd-spec.md](../artifact-templates/prd-spec.md)。

实现：`validators/spec_md_rules.py`（读 run 目录 `spec.md`，对照 `spec.json`）。

| rule_id | 严重度 | 必检 | 触发条件 | 检查对象 | 判定 |
|---------|--------|------|----------|----------|------|
| `SPEC-301` | warn | 是 | — | `spec.md` | 须含 `## 概述` |
| `SPEC-302` | warn | 是 | — | `spec.md` | 须含 `## 验收标准` |
| `SPEC-303` | warn | 是 | — | `spec.md` | 须含 `## 范围` |
| `SPEC-304` | warn | 是 | — | `spec.md` 正文 | 出现的 `AC-*` id 与 `spec.json` 一致 |
| `SPEC-305` | warn | 是 | — | `spec.md` 文末元数据 | 含 `task_profile`、`revision` |
| `SPEC-306` | warn | 条件 | `success_metrics` 非空 | `spec.md` | 须含 `## 业务指标` |
| `SPEC-307` | warn | 是 | — | `spec.md` | 须含 `## 功能` |
| `SPEC-308` | warn | 是 | — | `spec.md` | 须含 `## 稳定性、性能与数据一致性` |
| `SPEC-309` | warn | 是 | — | `spec.md` | 须含 `## 术语与领域概念` |
| `SPEC-310` | warn | 是 | — | `spec.md` | 须含 `## 背景与上下文` |
| `SPEC-311` | warn | 是 | — | `spec.md` | 须含 `## 用户故事` |
| `SPEC-312` | warn | 是 | — | `spec.md` | 须含 `## 需求池` |
| `SPEC-313` | warn | 是 | — | `spec.md` | 须含 `## 约束` |

**失败：** `route_after_spec_validate` → **pm**；violations 注入 PM prompt。
