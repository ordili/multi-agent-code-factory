# multi-agent-code-factory

用 **LangGraph** 编排 PM、Architect、Developer、QA、Reviewer 五个 Agent，把自然语言需求变成**可测试的业务代码**，并在本仓库留下完整审计轨迹。

**V1** 是通用、领域无关的引擎：语言与工具链由 **Profile** 注入（如 Python Todo CLI、Java、Rust）。具体业务领域（如套利）在 **V2** `[domains/](domains/README.md)`。

## 它能做什么


| 输入                               | 输出                                                           |
| -------------------------------- | ------------------------------------------------------------ |
| 自然语言需求（如「实现命令行 Todo」）            | Profile.`code_root` 下的源码与测试（默认 `../generated/<profile-id>/`） |
| Profile（语言、`test_command`、校验规则等） | `docs/runs/<task_id>/` 下的结构化 JSON + 人读 MD（spec、design、测试报告等） |


与「单次让 LLM 写代码」的区别：需求与设计先过**程序校验**（`spec_validate` / `design_validate`），实现后由 **QA 真实跑测**（非 LLM 编造），失败可自动回路修订，全程可审计。

## 配置怎么分（Profile vs `.env`）


| 你想配置什么                                 | 放哪里                                                                   |
| -------------------------------------- | --------------------------------------------------------------------- |
| Python / Java / Go 等**技术栈**、怎么跑测试、校验规则 | **Profile**：`multi_agent_code_factory/profiles/<id>.yaml`             |
| 生成代码写到哪里（语言默认目录）                       | **Profile** 的 `code_root`（如 `../generated/python`）；多项目用 `--code-root` |
| LLM **API Key**、本机模型名                  | `**.env`**（复制自 `.env.example`）或 shell 环境变量                            |
| 回路重试次数等**工厂全局**默认                      | `config/autonomy_policy.yaml`；本机可再用 `FACTORY_`* 覆盖                    |
| 这一次做什么需求                               | CLI：`--task-id` + 引号里的自然语言                                            |


选栈：`--profile <语言>`（V1：`python`、`go`、`java`、`rust`、`solidity`）；配 LLM：在 `.env` 设 `FACTORY_LLM_PROVIDER`、`FACTORY_LLM_MODEL`，并填**当前厂商**对应 API Key（如 `DEEPSEEK_API_KEY`）。详见 [profiles/README.md](multi_agent_code_factory/profiles/README.md)。

## 快速开始（Stub，无需 API Key）

**环境：** Python 3.11+

```bash
pip install -e ".[dev]"
```

默认使用 **Stub 模式**（固定 fixture，不调用 LLM），用于验证流水线与本地开发：

```bash
python -m multi_agent_code_factory run \
  --profile python \
  --task-id calculator \
  "实现一个支持加减乘除的计算器"
```

> **Windows（PowerShell）**：不要用 bash 的 `\` 续行；请写单行，或用反引号 `` ` `` 续行。

成功时终端输出 `status=completed`。然后可查看：


| 路径                        | 内容                                                            |
| ------------------------- | ------------------------------------------------------------- |
| `docs/runs/calculator/`   | 本次 run 的 spec、design、test_report、review、`run_meta.json` 等     |
| `../generated/python/`    | 默认生成代码目录（仓库外）；多项目可加 `--code-root ../generated/calculator` |




## 使用真实 LLM（可选）

安装 LLM 依赖并配置厂商（`deepseek` / `openai` / `anthropic` / `ollama`）：

```bash
pip install -e ".[llm]"
cp .env.example .env   # Windows: copy .env.example .env
# 编辑 .env：FACTORY_LLM_PROVIDER、FACTORY_LLM_MODEL、对应厂商 API Key
```

CLI 启动时会自动加载仓库根目录的 `.env`（已设置的 shell 环境变量优先）。`--live` 模式下，Ollama 会在 pipeline 启动前做 **preflight**（探测模型是否可响应），失败时提前报错并给出修复提示。

### 云 API（DeepSeek 等）

```env
FACTORY_LLM_PROVIDER=deepseek
FACTORY_LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=sk-...
```

### 本地 / VM Ollama

```env
FACTORY_LLM_PROVIDER=ollama
FACTORY_LLM_MODEL=qwen3.5:9b
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_NUM_CTX=8192
OLLAMA_NUM_PREDICT=4096
OLLAMA_REASONING=false
```

- 先 `ollama pull qwen3.5:9b`（或 `.env` 里配置的模型）。
- **`OLLAMA_BASE_URL` 请用 `127.0.0.1`**，不要用 `localhost`（Windows 上 `localhost` 可能走 IPv6 导致 HTTP 502）。
- CPU 推理较慢：单 Agent 常需数分钟，整轮 pipeline 可能 **30–90 分钟**。

指定输出目录并启用 live 模式：

```bash
python -m multi_agent_code_factory run \
  --profile python \
  --task-id calculator \
  --live \
  --log-level INFO \
  --code-root "D:\\code\\agent-out-code\\calculator" \
  "实现支持加减乘除的计算器"
```

常用参数：


| 参数                     | 说明                                            |
| ---------------------- | --------------------------------------------- |
| `--profile`            | 语言 Profile id：`python`                        |
| `--task-id`            | 本次 run 标识，产物写入 `docs/runs/<task_id>/`         |
| `--stub`               | 强制 Stub（默认行为）                                 |
| `--live`               | 真实 LLM（需当前 `FACTORY_LLM_PROVIDER` 对应配置）       |
| `--code-root`          | 覆盖 Profile 的 `code_root`                      |
| `--log-level`          | 日志级别（默认 `INFO`；或 `.env` 的 `FACTORY_LOG_LEVEL`） |
| `--max-impl-retries` 等 | 覆盖回路次数，见 `config/autonomy_policy.yaml`        |


环境变量摘要：

| 变量 | 说明 |
| ---- | ---- |
| `FACTORY_LLM_PROVIDER` | 厂商：`deepseek` / `openai` / `anthropic` / `ollama` |
| `FACTORY_LLM_MODEL` | 模型 id（如 `deepseek-chat`、`qwen3.5:9b`） |
| `DEEPSEEK_API_KEY` 等 | 云厂商 API Key（未用留空） |
| `OLLAMA_BASE_URL` | Ollama 地址（推荐 `http://127.0.0.1:11434`） |
| `OLLAMA_NUM_CTX` / `OLLAMA_NUM_PREDICT` / `OLLAMA_REASONING` | Ollama 推理调优（见 `.env.example`） |
| `FACTORY_LOG_LEVEL` | 默认日志级别（CLI `--log-level` 可覆盖） |
| `FACTORY_MAX_IMPL_RETRIES` 等 | 覆盖 `config/autonomy_policy.yaml` 回路默认 |

集成测试（需 API Key，CI 默认跳过）：

```bash
pytest tests/integration/test_todo_cli_e2e.py -m integration
```

## GCP / Linux VM 一键运行

在已安装 Ollama 的 VM 上，可用脚本拉最新代码并跑 live pipeline：

```bash
chmod +x scripts/vm-run-pipeline.sh scripts/vm-run-calculator.sh

# 通用：pull + venv + pip install + live run
./scripts/vm-run-pipeline.sh --task-id calculator "实现支持加减乘除的计算器"

# 计算器快捷入口（DEBUG 日志）
./scripts/vm-run-calculator.sh
```

脚本默认代码输出到 `/data/generated/<task-id>`；需事先配置仓库根目录 `.env`（Ollama 同机时用 `OLLAMA_BASE_URL=http://127.0.0.1:11434`）。详见 `scripts/vm-run-pipeline.sh` 头部注释。



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


| 层级       | 名称                             | 说明                      |
| -------- | ------------------------------ | ----------------------- |
| 仓库       | `multi-agent-code-factory`     | 引擎、配置、设计文档、run 审计       |
| Python 包 | `multi_agent_code_factory`     | LangGraph 流水线运行时        |
| 生成代码     | Profile.`code_root`（**须在仓库外**） | 如 `../generated/python` |


```text
multi-agent-code-factory/
├── multi_agent_code_factory/   # 引擎（graph、agents、validators、schemas、tools）
│   └── profiles/               # 语言 Profile（_base/common.yaml + python|go|…）
├── config/                     # 全局策略 autonomy_policy.yaml
├── scripts/                    # VM 部署与 pipeline 脚本（vm-run-pipeline.sh 等）
├── .env.example                # 本机密钥与可选 FACTORY_*（复制为 .env）
├── docs/
│   ├── design/                 # 设计 Spec（架构、Schema、实现计划）
│   └── runs/<task_id>/         # 单次 run 审计产物
└── domains/                    # V2 领域（当前不纳入 V1 验收）

../generated/                   # 生成代码根（Profile.code_root 指向，不在本仓库）
```



## 文档


| 文档                                                                                                         | 适合谁                   |
| ---------------------------------------------------------------------------------------------------------- | --------------------- |
| [docs/README.md](docs/README.md)                                                                           | 文档总览与易混淆对照            |
| [docs/design/00-master-overview.md](docs/design/00-master-overview.md)                                     | 项目目标与 V1/V2 边界        |
| [docs/design/pipeline/multi-agent-pipeline-design.md](docs/design/pipeline/multi-agent-pipeline-design.md) | 流水线主线（角色、路由、产物）       |
| [docs/design/pipeline/implementation-plan.md](docs/design/pipeline/implementation-plan.md) | V1 实现阶段与 PR 拆分        |
| [docs/design/pipeline/P1-backlog.md](docs/design/pipeline/P1-backlog.md) | P1 待办汇总（可勾选 checklist） |
| [docs/design/pipeline/README.md](docs/design/pipeline/README.md)                                           | Profile、Schema、示例细目索引 |
| [multi_agent_code_factory/profiles/README.md](multi_agent_code_factory/profiles/README.md)                 | 内置 Profile 列表         |


V2 领域（如套利）：[domains/README.md](domains/README.md)

## 开发贡献

```bash
pip install -e ".[dev]"
python -m ruff check . && python -m ruff format --check .
python -m pytest -q
python -m mypy multi_agent_code_factory
```

代码规范：[docs/design/pipeline/python-style.md](docs/design/pipeline/python-style.md)