# multi-agent-code-factory

**Multi-agent code factory** — 多 Agent 协作、流水线式生成可部署的业务代码。

| 层级 | 名称 | 说明 |
|------|------|------|
| 仓库 | `multi-agent-code-factory` | 引擎、配置、设计文档、run 审计 |
| Python 包 | `multi_agent_code_factory` | LangGraph 流水线运行时 |
| 生成代码 | Profile.`code_root`（仓库外） | 如 `../generated/default`、`../arb-robot` |

## 文档入口

- [总览](docs/superpowers/specs/00-master-overview.md)
- [流水线设计](docs/superpowers/specs/multi-agent-pipeline-design.md)
- [工厂细目索引](docs/superpowers/specs/factory/README.md)

## 运行（规划）

```bash
python -m multi_agent_code_factory run --profile default --task-id todo-cli "实现命令行 Todo"
```

## 目录结构

```text
multi-agent-code-factory/
├── multi_agent_code_factory/     # 引擎
├── config/
└── docs/
    ├── superpowers/specs/        # 设计 Spec
    └── factory/runs/               # 单次 run 产物

../generated/                       # 生成代码（Profile.code_root，不在本仓库）
../arb-robot/                       # 套利业务示例
```
