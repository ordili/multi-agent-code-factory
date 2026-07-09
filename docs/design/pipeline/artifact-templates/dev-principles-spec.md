# dev-principles-spec.md — 生成代码通用工程原则

> **状态：** 定稿 · [artifact-templates 索引](./README.md)  
> **适用范围：** 所有 Profile 写入 `code_root` 的**业务代码**（语言无关）  
> **语言细则：** 各 Profile `{language}-style-snippet.txt`；Python 详见 [python-style.md](../python-style.md)  
> **注入：** Developer 节点 system prompt（`dev-principles-snippet.txt`）  
> **非 Run 落盘产物：** 不生成 `dev-principles.md`；遵守情况体现在 `{code_root}/**` 与 `dev_manifest.json`

---

## 文档定位

| 对比 | 本规范 | `design-spec.md` | `{language}-style-snippet` |
|------|--------|------------------|----------------------------|
| 阶段 | **实现** | 设计 | 实现 |
| 读者 | Developer、Reviewer、HITL | Architect、Developer | Developer（LLM） |
| 内容 | README、SRP、项目卫生 | 模块 API、错误码、dev_tasks | PEP8、Ruff、pytest 等 |
| 产物 | 约束 `code_root` 目录树 | `design.json` / `design.md` | prompt 注入 |

**冲突时：** 通用原则（本文）优先于风格偏好；**工具链命令**以 Profile.`toolchain` 与语言 style 为准。

---

## §1 必备项目文件

生成的新项目 **必须** 包含：

| 文件 / 目录 | 要求 |
|-------------|------|
| **`README.md`** | **必须。** 至少含：项目简介、安装/构建、用法（CLI 示例或 API 入口）、如何跑测试 |
| **依赖清单** | 按语言：`pyproject.toml` / `go.mod` / `pom.xml` / `Cargo.toml` / `foundry.toml` 等 |
| **测试目录** | 与 `design.test_strategy` 及 Profile.`toolchain.test_dir_glob` 一致（如 `tests/`、`*_test.go`） |
| **源码目录** | 与 `design.file_plan` / `design.modules[]` 一致；避免单文件堆砌全部逻辑 |

可选（Spec 明确要求时）：`LICENSE`、`CHANGELOG.md`、`.env.example`（无真实密钥）。

---

## §2 架构原则

### 2.1 单一职责（SRP）

- 每个函数、类、模块 **只做一件事**，且命名能反映该职责。
- **分离** I/O（读写文件/网络）、解析/序列化、业务规则；禁止 god module / god class。
- 模块边界与 `design.modules[]` / `design.dev_tasks[]` 对齐；一个 dev_task 对应一组内聚变更。

### 2.2 依赖方向

- 业务逻辑 **不依赖** CLI 框架细节；CLI 层薄，调用 domain/store。
- 优先组合优于继承；避免循环 import / 循环包依赖。

### 2.3 可测试性

- 核心逻辑须能在无网络、无真实外部服务的单元测试中验证（除非 Spec AC 明确要求集成测试）。
- 禁止在 domain 层直接 `print` 调试；CLI 负责用户可见输出。

---

## §3 代码质量

| 原则 | 说明 |
|------|------|
| 显式错误 | 预期失败返回错误或抛领域异常；禁止静默吞异常 |
| 输入校验 | 校验 CLI 参数、文件内容、外部 payload；失败信息对用户可读 |
| 资源管理 | 文件、锁、连接使用语言惯用方式释放（如 Python `with`） |
| 命名 | 见各语言 style snippet；名称与 design 模块/接口一致 |
| 规模 | 单文件不宜过长；超过 ~300 行应考虑拆分（除非 generated CLI 单入口特例） |

---

## §4 安全与配置

- **禁止** 硬编码 API Key、私钥、token；使用环境变量或 Spec 允许的配置文件。
- **禁止** `eval` / `exec` 处理不可信输入（Python 等）。
- **禁止** 工厂 Agent 读写业务凭证文件；生成代码亦不得提交 `.env` 含真实密钥。
- 子进程默认不启用 shell（除非 Spec / design 明确要求）。

---

## §5 测试纪律

- 每个 **业务模块**（非纯 `__init__` / 配置）须有对应测试文件或测试套件。
- 测试须覆盖 Spec **`acceptance_criteria`** 与 design **附录 D / test_cases** 中的 P0 场景。
- 测试命名表达行为与条件；失败信息须能定位到文件与行（配合 QA `TestReport`）。
- 与 QA **`tests_missing`** 检测一致：缺测路径会导致实现环回 Developer（Profile.`auto_generate_tests` 时提示补测）。

---

## §6 文档

### 6.1 README.md 最低章节

| 章节 | 内容 |
|------|------|
| 简介 | 一句话 + 与 Spec 标题对应 |
| 安装 | 依赖安装命令（与 Profile.`toolchain.setup` 一致或更简单） |
| 用法 | CLI 子命令示例或主 API 用法 |
| 测试 | 跑测试与 lint 的命令（与 Profile.`toolchain` 一致） |

### 6.2 代码内文档

- **公开** API（export / public 函数与类）须有语言惯用文档注释（见各语言 style）。
- CLI `--help` 文案与 README 用法 **不矛盾**。

---

## §7 与流水线角色关系

| 角色 | 如何使用本文 |
|------|----------------|
| **Developer** | system prompt 注入 `dev-principles-snippet.txt` |
| **QA** | 不读本文；跑 `toolchain.test_command` + `tests_missing` |
| **Reviewer** | 对照 README、测试覆盖、SRP；见 [review-spec.md](./review-spec.md) |
| **Architect** | 在 `file_plan` / `test_strategy` 中体现 README 与测试布局 |

---

## §8 实现落点

| 项 | 路径 |
|----|------|
| 本文（定稿） | `docs/design/pipeline/artifact-templates/dev-principles-spec.md` |
| LLM 摘要 | `multi_agent_code_factory/profiles/_shared/prompts/dev-principles-snippet.txt` |
| 注入逻辑 | `agents/llm/prompt/builder.py`、`style_snippet.py` |
| Python 语言细则 | [python-style.md](../python-style.md) |

---

## 附录：snippet 与本文对应

`dev-principles-snippet.txt` 为本文 §1–§6 的 condensed bullet，供 token 受限的 Developer 调用；更新原则时 **先改本文，再同步 snippet**。
