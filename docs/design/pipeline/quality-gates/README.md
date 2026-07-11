# 产物校验与 HITL — 索引

## 依赖上游文档（只读）

审查 / 修订本目录规则时 **仅以本表及正文为准**；不引用 `validators/` 等下游实现。字段定义查 artifact-schemas，章节写法查 artifact-templates。


| 分类        | 上游文档                                                                                  | 定位                          |
| --------- | ------------------------------------------------------------------------------------- | --------------------------- |
| **总设计**   | [multi-agent-pipeline-design.md](../multi-agent-pipeline-design.md) | 系统的总体设计书 |
| **JSON 契约** | [artifact-schemas/README.md](../artifact-schemas/README.md)                         | 字段与「是否必填」交付 intent        |
| **人读模板**  | [artifact-templates/README.md](../artifact-templates/README.md)                       | `prd.md` / `design.md` 格式  |
| **产出契约**  | [validation-report-spec.md](../artifact-schemas/validation-report-spec.md)            | `ValidationReport` 结构       |
| **运行配置**  | [profiles.md](../profiles.md)                                                       | `validation.*` YAML 载体      |


---

> **主线：** [multi-agent-pipeline-design.md §4.1.2](../multi-agent-pipeline-design.md#412-产物校验与-hitlpm--architect)  
> **原则：** **规则校验（程序）** 为主、**可选人工 HITL** 为辅；均在 **Developer 写代码之前** 拦截 PM / Architect 产物。  
> **实现：** `multi_agent_code_factory/validators/` · [`validation-report-spec.md`](../artifact-schemas/validation-report-spec.md)

## 文档职责

本目录定义 **怎么算过关**（`rule_id`、严重度、触发条件、判定）。**不重复** JSON 字段定义与人读章节写法。

| 上游（只读引用） | 本目录 | 下游 |
|------------------|--------|------|
| [artifact-schemas/](../artifact-schemas/README.md) — JSON 字段、类型、「是否必填」交付 intent | **quality-gates/** — `PRD-*` / `DES-*` 规则正文 | `validators/` 实现 · Profile `validation.*` |

- JSON 契约 → 引 **artifact-schemas**（如 [design-spec.md](../artifact-schemas/design-spec.md)）  
- 人读格式 → 引 **artifact-templates**（规则不展开写作篇幅）  
- schema「是否必填 = 是」**≠** 每条都有 `DES-*` non-empty；见 [design-validate §JSON 契约 vs 规则](./design-validate.md#json-契约-vs-规则与-schema是否必填对齐)

## 文档地图

| 文档 | 内容 |
|------|------|
| [prd-validate.md](./prd-validate.md) | `prd_validate` · `PRD-*` · Run `prd.md` |
| [design-validate.md](./design-validate.md) | `design_validate` · `DES-*` · Run `design.json` / `design.md` / `*.mmd` |
| [hitl.md](./hitl.md) | `prd_hitl` / `design_hitl` / `deploy_hitl` / `escalation_hitl` · 与 Reviewer 分工 |

**rule_id 合计（定稿）：** **106** 条已定义（`PRD-*` **49** · `DES-*` **57**；HITL 无独立 rule_id）。

**条件规则：** 部分 `DES-*` 按 prd / design 字段信号决定是否要求非空，见 [design-validate.md §1](./design-validate.md#1-designjsonerror--warn) 各条「触发条件」；prd 侧见 [prd-validate.md §prd→design](./prd-validate.md#prd--design-传导只读)。

**Run 落盘 vs 格式规范：** Run 使用短 basename（`prd.json` / `design.json`）；字段定义见 **artifact-schemas**；章节模板见 **artifact-templates**。

---

## 0. 命名约定

**统一模式：** `{产物}_{动作}`。程序校验用 `_validate`，人工审批用 `_hitl`（与 `prd_hitl` 对称）。

| 图节点 | 模块 | 类型 | Run 产物 |
|--------|------|------|----------|
| **`prd_validate`** | `nodes/prd_validate.py` | 程序规则 | `prd_validation.json` |
| **`prd_hitl`** | `nodes/prd_hitl.py` | 人工 interrupt | `hitl.json`（`stage=prd`） |
| **`design_validate`** | `nodes/design_validate.py` | 程序规则 | `design_validation.json` |
| **`design_hitl`** | `nodes/design_hitl.py` | 人工 interrupt | `hitl.json`（`stage=design`） |
| **`deploy_hitl`** | `nodes/deploy_hitl.py` | 人工 interrupt | `hitl.json`（`stage=deploy`） |
| **`escalation_hitl`** | `nodes/escalation_hitl.py` | 人工 interrupt（loop 触顶） | `hitl.json`（`stage=escalation`） |

| Profile 配置块 | 说明 |
|----------------|------|
| **`validation`** | `prd` / `design` 规则开关（原 `gates`，已废弃） |
| **`hitl`** | deploy 阶段敏感路径 / flags（供 `deploy_hitl` 判定） |

| 其它 | 约定 |
|------|------|
| **`ValidationReport.target`** | `prd` \| `design`（校验对象；原字段名 `gate` 已废弃） |
| **`on_limit_exceeded`** | `fail` \| `escalation_hitl`（loop 触顶；`deploy_hitl` / `human_gate` 为旧别名，已废弃） |
| **Reviewer** | QA 后 LLM 审查（`reviewer`），**不是** HITL 节点 |

**五 Agent 命名：** 正文用 PM / Architect / Developer / QA / Reviewer；代码与路由用 `role_id` — 详见主线 [§3.1](../multi-agent-pipeline-design.md#31-角色命名约定)。

---

## 1. 在流水线中的位置

```text
PM → prd_validate → [prd_hitl?] → Architect → design_validate → [design_hitl?] → Developer → QA → Reviewer → [deploy_hitl?] → Deploy
```

| 节点 | 类型 | 失败 / 驳回 |
|------|------|-------------|
| **prd_validate** | 程序 | → **PM** |
| **prd_hitl** | 人工 | 驳回 → **PM** |
| **design_validate** | 程序 | → **Architect** |
| **design_hitl** | 人工 | 驳回 → **Architect** |
| **deploy_hitl** | 人工 | 部署 / 敏感变更（Reviewer 通过后） |

**可信度：** `TestReport` > `ValidationReport` > `HitlDecision` > `ReviewReport`（LLM）。

---

## 2. Profile 配置（`validation`）

```yaml
validation:
  prd:
    enabled: true
    block_on: error          # error | warn | never
    require_hitl: false
  design:
    enabled: true
    block_on: error
    require_hitl: false
    validate_mermaid: true
    require_hitl_if_flags: [touches_production]
```

| 字段 | 说明 |
|------|------|
| `enabled` | false 则跳过该 validate 节点（仍做 Pydantic 结构校验） |
| `block_on` | **`error`（默认）**：`passed=false` 时路由回 PM/Architect（prd/design 分别配置）。**warn 级 violation 不导致 `passed=false`**。`warn`：仍仅 error 计失败，且路由不检查 `block_on`（不阻断，仅落盘）。`never`：`passed` 恒为 true |
| `require_hitl` | 规则通过后是否强制 `prd_hitl` / `design_hitl` |
| `require_hitl_if_flags` | 命中 `design.hitl_flags` 时强制 `design_hitl` |
| `validate_mermaid` | 是否解析 Run 目录 `*.mmd`（**仅当** [DES-017](./design-validate.md#14-图diagrams) 触发时要求 sequence + flowchart；`default` Profile 为 **false**，见 [flow-spec.md](../artifact-templates/flow-spec.md)） |

**生产级 Profile 示例（P1）：** 可设 `validation.prd.require_hitl: true`、`validation.design.require_hitl: true`，并配置 `hitl.sensitive_globs` / `hitl.flags` 触发 `deploy_hitl`。

---

## 7. 实现落点

```text
multi_agent_code_factory/
├── validators/          # prd_rules.py, prd_md_rules.py, design_rules.py, design_md_rules.py, mermaid.py
├── nodes/
│   ├── prd_validate.py
│   ├── design_validate.py
│   ├── prd_hitl.py
│   ├── design_hitl.py
│   ├── deploy_hitl.py
│   ├── deploy.py
│   └── escalation_hitl.py   # P1；MVP 默认 on_limit_exceeded=fail
└── schemas/validation_report.py
```

完整目录见主线 [§6.2](../multi-agent-pipeline-design.md#62-multi_agent_code_factory-详解)。

---

## 8. 路由伪代码

**路由以实现为准：** [multi-agent-pipeline-design.md §4.3](../multi-agent-pipeline-design.md#路由伪代码以实现为准)（`graph_routing.py`）。本节不再重复；实现须与主线伪代码一致，含 `loop_limits` 触顶判断与 `route_after_review` 对 `approved` 的守卫。
