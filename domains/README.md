# 领域包（V2）

> **V1 范围：** 仅 [docs/design/pipeline/](../docs/design/pipeline/multi-agent-pipeline-design.md) 中的 **通用** 多 Agent 流水线。  
> **本目录：** 各业务领域的 **Profile 配置、prompts 与设计文档**，与引擎代码分离，**不纳入 V1 实现与验收**。

| 子目录 | 说明 | 状态 |
|--------|------|------|
| [arb/](./arb/) | DEX↔DEX 套利（`profile/arb.yaml` + 设计 spec） | V2 草案 |

## 目录约定

```text
domains/<name>/
├── README.md
├── profile/
│   ├── <id>.yaml
│   └── prompts/
└── design/
    └── *.md
```

新增领域：在本目录下新建 `<name>/`，配套 `profile/<id>.yaml`；引擎加载 Profile 时须包含 `domains/*/profile/*.yaml`（V2 实现）。
