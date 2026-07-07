# arb-factory — 研发流水线设计（套利领域）

> **V2 — 不在 V1 实现范围。** 保留草案备查；V1 见 [pipeline 主线](../../../docs/design/pipeline/multi-agent-pipeline-design.md)。  
> **依据：** [00-master-overview.md](../../../docs/design/00-master-overview.md)  
> **Profile 以：** [profile/arb.yaml](../profile/arb.yaml) **为准**  
> **本文：** 套利 Profile 领域约束与 HITL 规则（V2）

---

## 1. 流水线

与主线一致：[multi-agent-pipeline-design.md §1](../../../docs/design/pipeline/multi-agent-pipeline-design.md#1-设计结论)。套利差异仅在 §2–§4（Profile、`code_root`、HITL 规则）。

---

## 2. 角色与 Tool（套利 Profile）

| Agent（role_id） | 职责 | 可用 Tool | 禁止 |
|------------------|------|-----------|------|
| **PM**（`pm`） | PRD、验收标准 | 写 `docs/runs/<task_id>/` | 写业务代码 |
| **Architect**（`architect`） | 模块设计 | 写 design Artifact | 直接改 `code_root` 下实现 |
| **Developer**（`developer`） | Connector / Strategy | 写 `code_root`（默认 `../arb-robot/`）、linter | 部署、私钥 |
| **QA**（`qa`） | 自动化测试 | `run_tests` | 部署 |
| **Reviewer**（`reviewer`） | 安全审查 | 读 diff、测试报告 | 改代码 |

**arb Profile：** `validation.spec.require_hitl: true`、`validation.design.require_hitl: true`（须 P1 实现 `spec_hitl` / `design_hitl` interrupt 后方可端到端跑通）。

---

## 3. 目录结构

见 [multi-agent-pipeline-design.md §6.1](../../../docs/design/pipeline/multi-agent-pipeline-design.md#61-仓库总览)。摘要：

```text
multi_agent_code_factory/       # 引擎
domains/arb/profile/arb.yaml  # 本领域 Profile（V2）
../arb-robot/                   # code_root（仓库外）
docs/runs/                      # run 产物
```

---

## 4. 配置（HITL 与 loop_limits）

### 4.1 全局（`config/autonomy_policy.yaml`）

```yaml
multi_agent_code_factory:
  loop_limits:
    max_impl_retries: 3
    max_design_revisions: 2
    max_spec_revisions: 1
  max_hitl_rounds: 5
  on_limit_exceeded: fail   # fail | escalation_hitl（见主线 §4.4）
```

### 4.2 套利 Profile（`domains/arb/profile/arb.yaml`）

HITL 与产物校验由 **Profile** 注入（非 `autonomy_policy` 独立字段）：

```yaml
validation:
  spec:
    enabled: true
    require_hitl: true
  design:
    enabled: true
    require_hitl: true
    require_hitl_if_flags: [touches_production, prod_deploy_trading]
hitl:
  sensitive_globs:
    - "core/risk.py"
    - "core/executor.py"
    - "**/deploy/**"
  flags: [touches_production, prod_deploy_trading, risk_limit_changes]
```

详见 [profiles.md](../../../docs/design/pipeline/profiles.md)、[quality-gates.md](../../../docs/design/pipeline/quality-gates.md)。

---

## 5. 验收

- [ ] `python -m multi_agent_code_factory run --profile arb ...` 全链路跑通（**P1**：依赖 `spec_hitl` / `design_hitl` interrupt；Profile 路径 `domains/arb/profile/arb.yaml`）
- [ ] `spec_validate` / `design_validate` 失败可回 PM/Architect
- [ ] P1：`spec_hitl` / `design_hitl` / `deploy_hitl` 可暂停与恢复

术语见 [glossary.md](../../../docs/design/pipeline/references/glossary.md)。
