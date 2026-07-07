# multi-agent-code-factory

**Multi-agent code factory** — 多 Agent 协作、流水线式生成可部署的业务代码（**V1：通用领域无关引擎**）。

| 层级 | 名称 | 说明 |
|------|------|------|
| 仓库 | `multi-agent-code-factory` | 引擎、配置、设计文档、run 审计 |
| Python 包 | `multi_agent_code_factory` | LangGraph 流水线运行时 |
| 生成代码 | Profile.`code_root`（仓库外） | 如 `../generated/default` |

## 文档入口

- [文档总览](docs/README.md)
- [总览](docs/design/00-master-overview.md)
- [流水线设计](docs/design/pipeline/multi-agent-pipeline-design.md)
- [工厂细目索引](docs/design/pipeline/README.md)
- [Python 代码规范](docs/design/pipeline/python-style.md)

## 开发（Python 引擎）

```bash
pip install -e ".[dev]"
python -m ruff check . && python -m ruff format --check .
python -m pytest -q
python -m mypy multi_agent_code_factory
```

```bash
python -m multi_agent_code_factory run --profile default --task-id todo-cli "实现命令行 Todo"
```

## 目录结构

```text
multi-agent-code-factory/
├── multi_agent_code_factory/     # 引擎
├── config/
├── docs/
│   ├── design/                 # V1 设计 Spec
│   └── runs/                   # 单次 run 产物
└── domains/                    # V2 领域（Profile + 设计）

../generated/                       # 生成代码（Profile.code_root，不在本仓库）
```

V2 领域（如套利）：[domains/](domains/README.md)
