# 产物校验与 HITL — 索引

> **主线：** [multi-agent-pipeline-design.md §4.1.2](../multi-agent-pipeline-design.md#412-产物校验与-hitlpm--architect)  
> **原则：** **规则校验（程序）** 为主、**可选人工 HITL** 为辅；均在 **Developer 写代码之前** 拦截 PM / Architect 产物。  
> **实现：** `multi_agent_code_factory/validators/` · [`validation-report-spec.md`](../artifact-schemas/validation-report-spec.md)

## 文档职责

本目录定义 **怎么算过关**（`rule_id`、严重度、触发条件、判定）。**不重复** JSON 字段定义与人读章节写法。

| 上游（只读引用） | 本目录 | 下游 |
|------------------|--------|------|
| [artifact-schemas/](../artifact-schemas/README.md) — JSON 字段、类型、「是否必填」交付 intent | **quality-gates/** — `SPEC-*` / `DES-*` 规则正文 | `validators/` 实现 · Profile `validation.*` |

- JSON 契约 → 引 **artifact-schemas**（如 [design-spec.md](../artifact-schemas/design-spec.md)）  
- 人读格式 → 引 **artifact-templates**（规则不展开写作篇幅）  
- schema「是否必填 = 是」**≠** 每条都有 `DES-*` non-empty；见 [design-validate §JSON 契约 vs 规则](./design-validate.md#json-契约-vs-规则与-schema是否必填对齐)

## 文档地图

| 文档 | 内容 |
|------|------|
| [spec-validate.md](./spec-validate.md) | `spec_validate` · `SPEC-*` · Run `spec.md` |
| [design-validate.md](./design-validate.md) | `design_validate` · `DES-*` · Run `design.json` / `design.md` / `*.mmd` |
| [hitl.md](./hitl.md) | `spec_hitl` / `design_hitl` / `deploy_hitl` / `escalation_hitl` · 与 Reviewer 分工 |

**rule_id 合计（定稿）：** **106** 条已定义（`SPEC-*` **44** · `DES-*` **62** = **57** 活跃 + **5** 废弃/合并；HITL 无独立 rule_id）。

**条件规则 / 任务 tier：** 部分 `DES-*`（如 013/014/017）按 spec + design 推断是否要求非空，见 [design-validate.md §4.1](./design-validate.md#41-json-结构error--warn) 与 `validators/task_tier.py`。spec 侧传导见 [spec-validate.md §spec→design](./spec-validate.md#spec--design-传导只读)。

**规范 vs 实现：** [design-validate.md §规范与实现对照](./design-validate.md#规范与实现对照) 列出定稿规则与当前 `validators/` 已知偏差（改代码时消项，不在此目录改规范迁就实现）。

**Run 落盘 vs 格式规范：** Run 使用短 basename（`spec.json` / `design.json`）；字段定义见 **artifact-schemas**；章节模板见 **artifact-templates**。

---

## 0. 命名约定

**统一模式：** `{产物}_{动作}`。程序校验用 `_validate`，人工审批用 `_hitl`（与 `spec_hitl` 对称）。

| 图节点 | 模块 | 类型 | Run 产物 |
|--------|------|------|----------|
| **`spec_validate`** | `nodes/spec_validate.py` | 程序规则 | `spec_validation.json` |
| **`spec_hitl`** | `nodes/spec_hitl.py` | 人工 interrupt | `hitl.json`（`stage=spec`） |
| **`design_validate`** | `nodes/design_validate.py` | 程序规则 | `design_validation.json` |
| **`design_hitl`** | `nodes/design_hitl.py` | 人工 interrupt | `hitl.json`（`stage=design`） |
| **`deploy_hitl`** | `nodes/deploy_hitl.py` | 人工 interrupt | `hitl.json`（`stage=deploy`） |
| **`escalation_hitl`** | `nodes/escalation_hitl.py` | 人工 interrupt（loop 触顶） | `hitl.json`（`stage=escalation`） |

| Profile 配置块 | 说明 |
|----------------|------|
| **`validation`** | `spec` / `design` 规则开关（原 `gates`，已废弃） |
| **`hitl`** | deploy 阶段敏感路径 / flags（供 `deploy_hitl` 判定） |

| 其它 | 约定 |
|------|------|
| **`ValidationReport.target`** | `spec` \| `design`（校验对象；原字段名 `gate` 已废弃） |
| **`on_limit_exceeded`** | `fail` \| `escalation_hitl`（loop 触顶；`deploy_hitl` / `human_gate` 为旧别名，已废弃） |
| **Reviewer** | QA 后 LLM 审查（`reviewer`），**不是** HITL 节点 |

**五 Agent 命名：** 正文用 PM / Architect / Developer / QA / Reviewer；代码与路由用 `role_id` — 详见主线 [§3.1](../multi-agent-pipeline-design.md#31-角色命名约定)。

---

## 1. 在流水线中的位置

```text
PM → spec_validate → [spec_hitl?] → Architect → design_validate → [design_hitl?] → Developer → QA → Reviewer → [deploy_hitl?] → Deploy
```

| 节点 | 类型 | 失败 / 驳回 |
|------|------|-------------|
| **spec_validate** | 程序 | → **PM** |
| **spec_hitl** | 人工 | 驳回 → **PM** |
| **design_validate** | 程序 | → **Architect** |
| **design_hitl** | 人工 | 驳回 → **Architect** |
| **deploy_hitl** | 人工 | 部署 / 敏感变更（Reviewer 通过后） |

**可信度：** `TestReport` > `ValidationReport` > `HitlDecision` > `ReviewReport`（LLM）。

---

## 2. Profile 配置（`validation`）

```yaml
validation:
  spec:
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
| `block_on` | `error` 阻断；`warn` 只记录；`never` 仅落盘报告 |
| `require_hitl` | 规则通过后是否强制 `spec_hitl` / `design_hitl` |
| `require_hitl_if_flags` | 命中 `design.hitl_flags` 时强制 `design_hitl` |
| `validate_mermaid` | 是否解析 Run 目录 `*.mmd`（须含可识别的 sequence + flowchart；见 [flow-spec.md](../artifact-templates/flow-spec.md)） |

**生产级 Profile 示例（P1）：** 可设 `validation.spec.require_hitl: true`、`validation.design.require_hitl: true`，并配置 `hitl.sensitive_globs` / `hitl.flags` 触发 `deploy_hitl`。

---

## 7. 实现落点

```text
multi_agent_code_factory/
├── validators/          # spec_rules.py, spec_md_rules.py, design_rules.py, design_md_rules.py, mermaid.py
├── nodes/
│   ├── spec_validate.py
│   ├── design_validate.py
│   ├── spec_hitl.py
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
