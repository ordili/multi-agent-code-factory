# 产物校验与 HITL — 索引

> **主线：** [multi-agent-pipeline-design.md §4.1.2](../multi-agent-pipeline-design.md#412-产物校验与-hitlpm--architect)  
> **原则：** **规则校验（程序）** 为主、**可选人工 HITL** 为辅；均在 **Developer 写代码之前** 拦截 PM / Architect 产物。  
> **实现：** `multi_agent_code_factory/validators/` · [`validation-report-spec.md`](../artifact-schemas/validation-report-spec.md)  
> **规格基线（定稿）：** [artifact-schemas/*-spec.md](../artifact-schemas/README.md)（JSON 契约）· [artifact-templates/*-spec.md](../artifact-templates/README.md)（人读 MD / Mermaid）

## 文档地图

| 文档 | 内容 |
|------|------|
| [spec-validate.md](./spec-validate.md) | `spec_validate` · `SPEC-*` · Run `spec.md` ↔ [`prd-spec.md`](../artifact-templates/prd-spec.md) |
| [design-validate.md](./design-validate.md) | `design_validate` · `DES-*` · Run `design.md` / `*.mmd` |
| [hitl.md](./hitl.md) | `spec_hitl` / `design_hitl` / `deploy_hitl` / `escalation_hitl` · 与 Reviewer 分工 |

**rule_id 合计：** **106** 条（`SPEC-*` **44** · `DES-*` **62**；HITL 节点无独立 rule_id）。

**Run 落盘 vs 格式规范：** Run 使用短 basename（`spec.json` / `spec.md`）；格式与 JSON 契约见 [`prd-spec.md`](../artifact-schemas/prd-spec.md)（schemas）与 [`prd-spec.md`](../artifact-templates/prd-spec.md)（templates）。规则清单不在此重复字段定义。

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
├── validators/          # spec_rules.py, spec_md_rules.py (P1), design_rules.py, mermaid.py (P1)
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
