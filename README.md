# multi-agent-code-factory

用 **LangGraph** 编排 PM、Architect、Developer、QA、Reviewer 五个 Agent，把自然语言需求变成**可测试的业务代码**，并在本仓库留下完整审计轨迹。

**V1** 是通用、领域无关的引擎：语言与工具链由 **Profile** 注入（如 Python Todo CLI、Java、Rust）。具体业务领域（如套利）在 **V2** [`domains/`](domains/README.md)。

## 它能做什么

| 输入 | 输出 |
|------|------|
| 自然语言需求（如「实现命令行 Todo」） | Profile.`code_root` 下的源码与测试（默认 `../generated/<profile-id>/`） |
| Profile（语言、`test_command`、校验规则等） | `docs/runs/<task_id>/` 下的结构化 JSON + 人读 MD（spec、design、测试报告等） |

与「单次让 LLM 写代码」的区别：需求与设计先过**程序校验**（`spec_validate` / `design_validate`），实现后由 **QA 真实跑测**（非 LLM 编造），失败可自动回路修订，全程可审计。

## 快速开始（Stub，无需 API Key）

**环境：** Python 3.11+

```bash
pip install -e ".[dev]"
```

默认使用 **Stub 模式**（固定 fixture，不调用 LLM），用于验证流水线与本地开发：

```bash
python -m multi_agent_code_factory run \
  --profile default \
  --task-id todo-cli \
  "实现命令行 Todo"
```

成功时终端输出 `status=completed`。然后可查看：

| 路径 | 内容 |
|------|------|
| `docs/runs/todo-cli/` | 本次 run 的 spec、design、test_report、review、`run_meta.json` 等 |
| `../generated/default/` | `default` Profile 的生成代码目录（仓库外，相对本仓库根） |

## 使用真实 LLM（可选）

安装 LLM 依赖并配置 DeepSeek（OpenAI 兼容 API）：

```bash
pip install -e ".[llm]"
export DEEPSEEK_API_KEY=sk_...
```

指定输出目录并启用 live 模式：

```bash
python -m multi_agent_code_factory run \
  --profile default \
  --task-id todo-cli \
  --live \
  --code-root /path/to/output \
  "实现命令行 Todo：add/list/done，JSON 持久化，带 pytest"
```

常用参数：

| 参数 | 说明 |
|------|------|
| `--profile` | Profile id，见 [`multi_agent_code_factory/profiles/`](multi_agent_code_factory/profiles/) |
| `--task-id` | 本次 run 标识，产物写入 `docs/runs/<task_id>/` |
| `--stub` | 强制 Stub（默认行为） |
| `--live` | 真实 LLM（需 `DEEPSEEK_API_KEY`） |
| `--code-root` | 覆盖 Profile 的 `code_root` |
| `--max-impl-retries` 等 | 覆盖回路次数，见 `config/autonomy_policy.yaml` |

环境变量（可选）：`DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`；换模型可用 `FACTORY_CHAT_MODEL`（如 `openai:deepseek-chat`）或 `FACTORY_LLM_PROVIDER`；回路上限 `FACTORY_MAX_IMPL_RETRIES` 等。详见 [流水线设计 §9](docs/design/pipeline/multi-agent-pipeline-design.md#9-环境变量)。

集成测试（需 API Key，CI 默认跳过）：

```bash
pytest tests/integration/test_todo_cli_e2e.py -m integration
```

## 流水线概览

```text
用户需求
  → PM（spec）→ spec_validate
  → Architect（design）→ design_validate
  → Developer（写 code_root）→ QA（run_tests）→ Reviewer
  → [deploy_hitl?] → Deploy
```

校验失败或测试/审查不通过时，按 Profile 与 `loop_limits` 回到 PM / Architect / Developer 再试。设计见 [multi-agent-pipeline-design.md](docs/design/pipeline/multi-agent-pipeline-design.md)。

## 命名与目录

| 层级 | 名称 | 说明 |
|------|------|------|
| 仓库 | `multi-agent-code-factory` | 引擎、配置、设计文档、run 审计 |
| Python 包 | `multi_agent_code_factory` | LangGraph 流水线运行时 |
| 生成代码 | Profile.`code_root`（**须在仓库外**） | 如 `../generated/default` |

```text
multi-agent-code-factory/
├── multi_agent_code_factory/   # 引擎（graph、agents、validators、schemas、tools）
├── config/                     # 全局策略 autonomy_policy.yaml
├── docs/
│   ├── design/                 # 设计 Spec（架构、Schema、实现计划）
│   └── runs/<task_id>/         # 单次 run 审计产物
└── domains/                    # V2 领域（当前不纳入 V1 验收）

../generated/                   # 示例生成代码根（由 Profile.code_root 指向，不在本仓库）
```

## 文档

| 文档 | 适合谁 |
|------|--------|
| [docs/README.md](docs/README.md) | 文档总览与易混淆对照 |
| [docs/design/00-master-overview.md](docs/design/00-master-overview.md) | 项目目标与 V1/V2 边界 |
| [docs/design/pipeline/multi-agent-pipeline-design.md](docs/design/pipeline/multi-agent-pipeline-design.md) | 流水线主线（角色、路由、产物） |
| [docs/design/pipeline/implementation-plan.md](docs/design/pipeline/implementation-plan.md) | V1 实现阶段与 PR 拆分 |
| [docs/design/pipeline/README.md](docs/design/pipeline/README.md) | Profile、Schema、示例细目索引 |
| [multi_agent_code_factory/profiles/README.md](multi_agent_code_factory/profiles/README.md) | 内置 Profile 列表 |

V2 领域（如套利）：[domains/README.md](domains/README.md)

## 开发贡献

```bash
pip install -e ".[dev]"
python -m ruff check . && python -m ruff format --check .
python -m pytest -q
python -m mypy multi_agent_code_factory
```

代码规范：[docs/design/pipeline/python-style.md](docs/design/pipeline/python-style.md)
