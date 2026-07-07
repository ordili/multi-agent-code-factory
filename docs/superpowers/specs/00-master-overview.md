# Multi-Agent Code Factory — 总览

> **仓库：** `multi-agent-code-factory`  
> **引擎包：** `multi_agent_code_factory`  
> **日期：** 2026-07-06  
> **形态：** 独立新仓库，从零搭建  

---

## 目标

1. **实现 Multi-Agent Code Factory** — 用 Python 搭建多角色研发流水线（编排、Tool、测试、人工审批等），详见后续设计文档。

2. **用上述 Agent 生成可上线 PROD 的 DEX↔DEX 套利机器人代码** — 产出可部署、长期运行的套利业务代码（读价、价差、监控、下单等）。

---

## 关系

```text
多 Agent 研发流水线  →  生成 / 修改  →  DEX-DEX 套利机器人代码  →  部署 PROD
```

后续文档（工厂架构、运行时、实施计划等）**以本文档为目标依据**展开，本文档不展开技术细节。
