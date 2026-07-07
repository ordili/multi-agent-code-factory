# arb-factory — 研发流水线设计（套利领域）

> **依据：** [00-master-overview.md](./00-master-overview.md)  
> **实现真源：** [multi-agent-pipeline-design.md](./multi-agent-pipeline-design.md)  
> **本文：** 套利 Profile 领域约束与 HITL 规则

---

## 1. 流水线（摘要）

```text
PM → spec_validate → [spec_hitl?] → Architect → design_validate → [design_hitl?] → Developer → QA → Reviewer → deploy_hitl → Deploy
```

---

## 2. 角色与 Tool（套利 Profile）

| Agent（role_id） | 职责 | 可用 Tool | 禁止 |
|------------------|------|-----------|------|
| **PM**（`pm`） | PRD、验收标准 | 写 `docs/factory/runs/<task_id>/` | 写业务代码 |
| **Architect**（`architect`） | 模块设计 | 写 design Artifact | 直接改 `code_root` 下实现 |
| **Developer**（`developer`） | Connector / Strategy | 写 `code_root`（默认 `../arb-robot/`）、linter | 部署、私钥 |
| **QA**（`qa`） | 自动化测试 | `run_tests` | 部署 |
| **Reviewer**（`reviewer`） | 安全审查 | 读 diff、测试报告 | 改代码 |

**arb Profile：** `validation.spec.require_hitl: true`、`validation.design.require_hitl: true`。

---

## 3. 目录结构

见 [multi-agent-pipeline-design.md §6.1](./multi-agent-pipeline-design.md#61-仓库总览)。摘要：

```text
multi_agent_code_factory/       # 引擎；nodes/spec_validate.py、nodes/deploy_hitl.py 等
../arb-robot/        # code_root（仓库外；Profile arb）
docs/factory/runs/   # run 产物
```

---

## 4. 配置（`config/autonomy_policy.yaml`）

```yaml
multi_agent_code_factory:
  on_limit_exceeded: fail   # fail | escalation_hitl（见主线 §4.4）
  require_human_for:
    - prod_deploy_trading
    - risk_limit_changes
```

---

## 5. 验收

- [ ] `python -m multi_agent_code_factory run --profile arb ...` 全链路跑通
- [ ] `spec_validate` / `design_validate` 失败可回 PM/Architect
- [ ] P1：`spec_hitl` / `design_hitl` / `deploy_hitl` 可暂停与恢复

---

## 附录：术语

| 术语 | 含义 |
|------|------|
| **spec_validate / design_validate** | PM/Architect 程序规则节点 |
| **deploy_hitl** | 部署前人工审批节点（原 `human_gate`） |
| **Reviewer** | QA 后 LLM 审查 Agent（`role_id=reviewer`） |
