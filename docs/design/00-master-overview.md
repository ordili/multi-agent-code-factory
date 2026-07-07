# Multi-Agent Code Factory — 总览

> **仓库：** `multi-agent-code-factory`  
> **引擎包：** `multi_agent_code_factory`  
> **日期：** 2026-07-06  
> **形态：** 独立新仓库，从零搭建  
> **当前范围（V1）：** 通用多 Agent 研发流水线（领域无关，由 Profile 注入差异）

---

## 目标

**实现 Multi-Agent Code Factory** — 用 Python 搭建多角色研发流水线（编排、Tool、测试、人工审批等），通过不同 Profile 与 `code_root` 生成各语言、各领域的业务代码，详见 [pipeline/multi-agent-pipeline-design.md](./pipeline/multi-agent-pipeline-design.md)。

V1 以 **通用 Profile**（如 `default` Todo CLI、Java/Rust/Solidity 示例）验证引擎；**具体业务领域**（如套利）见 **V2** [domains/](../../domains/README.md)。

---

## 关系（V1）

```text
用户需求  →  多 Agent 研发流水线（Profile + code_root）  →  仓库外生成代码  →  测试 / 可选部署
```

---

## 文档入口

| 文档 | 说明 |
|------|------|
| [pipeline/multi-agent-pipeline-design.md](./pipeline/multi-agent-pipeline-design.md) | 流水线主线（角色、路由、产物、验收） |
| [pipeline/README.md](./pipeline/README.md) | Profile、Schema、示例等细目索引 |
| [domains/](../../domains/README.md) | **V2** 领域包（Profile + 设计，当前不实现） |

本文档不展开技术细节；细则以上述文档为准。
