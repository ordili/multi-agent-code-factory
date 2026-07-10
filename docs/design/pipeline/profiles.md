# Profile 与 Toolchain

## 依赖上游文档（只读）

审查 / 修订 Profile 说明时 **以本表及正文字段语义为准**；YAML 取值以仓库 `profiles/*.yaml` 为准。`validation.*` / `hitl` 字段语义见 [quality-gates/README.md](./quality-gates/README.md)（下游）。


| 分类       | 上游文档                                                                          | 定位                                      |
| -------- | ----------------------------------------------------------------------------- | --------------------------------------- |
| **总设计**  | [multi-agent-pipeline-design.md](./multi-agent-pipeline-design.md) | 系统的总体设计书 |
| **配置载体** | `multi_agent_code_factory/profiles/*.yaml`                                    | 字段默认值与示例 Profile                       |
| **领域（V2）** | [domains/README.md](../../../domains/README.md)                                | 领域 Profile 扩展                          |


---

> **配置以：** [`multi_agent_code_factory/profiles/`](../../../multi_agent_code_factory/profiles/) 下 `*.yaml` **为准**  
> **主线：** [multi-agent-pipeline-design.md §1.1](./multi-agent-pipeline-design.md#11-profile领域配置)  
> **V1 范围：** 本节矩阵与示例；**V2 领域 Profile** 见 [domains/](../../../domains/README.md)

流水线核心 **不含业务字段**。每次 run 指定 `profile`；语言、测试命令、HITL 均由 Profile 注入。

---

## 0. 配置分层（Profile vs `.env` vs 其它）

三类配置**不要混用**。选错位置会导致密钥进 Git、或团队无法共享同一技术栈默认值。

| 层级 | 载体 | 是否进 Git | 职责 | 典型内容 |
|------|------|------------|------|----------|
| **Profile** | `profiles/<id>.yaml` + `profiles/<id>/prompts/` | ✅ 是 | **技术栈与质量门**（可版本化、团队共享） | `language`、`toolchain`、`validation`、`hitl`、`prompts_dir`；`code_root` **路径约定**（推荐相对路径如 `../generated/<id>`） |
| **运行环境** | `.env`（本机）或 shell / CI 密钥 | ❌ `.env` 不进 | **厂商 + 模型 + 对应 API Key** | `FACTORY_LLM_PROVIDER`、`FACTORY_LLM_MODEL`；`DEEPSEEK_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`（未用留空） |
| **工厂全局策略** | `config/autonomy_policy.yaml` | ✅ 是 | **回路上限等团队默认** | `loop_limits`、`max_hitl_rounds`；可用 `FACTORY_*` env **覆盖**，默认仍以 YAML 为准 |
| **单次 run** | CLI 参数 | — | **本次任务** | `--task-id`、`user_request`、`--live`/`--stub`、`--code-root`（单次覆盖 Profile） |

**Profile 禁止：** API Key、token、私钥、个人绝对路径（除非团队统一约定且可接受）、自然语言需求、单次 `task-id`。

**`.env` 禁止：** `test_command`、校验规则、语言选择、Profile id——这些属于 Profile；应通过 `--profile` 选择栈，而不是在 env 里“换语言”。

**桥接约定：** Profile 可写 `code_root: ${FACTORY_CODE_ROOT}/java`——**模式在 Profile（进 Git）**，**值在 `.env`（本机）**。更简单时直接在 Profile 用 `../generated/<id>`，则无需在 `.env` 配置 `FACTORY_CODE_ROOT`。

配置优先级（高 → 低）：**CLI → `FACTORY_*` / LLM env → `autonomy_policy.yaml` → Profile 内建默认 → 代码默认**。

---

## 1. 配置字段

| 字段 | 说明 |
|------|------|
| `id` | Profile 标识，与 CLI `--profile` 一致 |
| `language` | `python` \| `go` \| `rust` \| `java` \| `solidity` 等 |
| `code_root` | **生成代码根目录**（须在 `multi-agent-code-factory` 仓库外；见 §1.1） |
| `prompts_dir` | 角色 prompt 目录 |
| `tools` | 注册到 Developer / QA 的 Tool 列表 |
| `toolchain` | 构建与测试命令集（§2） |
| `test_command` | **简写**：等价于 `toolchain.test_command` |
| `validation` | PM/Architect **规则校验**与可选 HITL（见 [quality-gates/README.md §2](./quality-gates/README.md#2-profile-配置validation)） |
| `context_schema` | 可选 JSON Schema，校验 `SpecArtifact.context` |
| `auto_generate_tests` | 缺测试时是否委托生成骨架（默认 false） |
| `hitl` | `sensitive_globs`、`flags`（deploy 阶段） |
| `subscriptions` | 可选；覆盖角色 `watch` 列表 |
| `sandbox` | 可选；`local` \| `docker` |
| `mcp_servers` | 可选；P2 |

**兼容：** 仅配置顶层 `test_command` → 等价于 `toolchain.test_command`；未指定 `test_parser` → 默认 `exit_code_only`。

**与 Spec 对齐：** PM 在 `spec.context.language` 声明语言；`spec_validate` 规则 `SPEC-006` 校验与 Profile.`language` 一致。

### 1.1 `code_root`（生成代码目录）

Developer / QA / Reviewer 读写业务源码的**唯一根路径**，由 Profile 配置，**不在 `multi-agent-code-factory` 仓库内**。

**解析规则（`profiles.py` 加载时）：**

| 输入形式 | 示例 | 解析方式 |
|----------|------|----------|
| 绝对路径 | `D:/code/todo-cli` | 原样 canonicalize |
| 相对路径 | `../generated/python` | 相对 **multi-agent-code-factory 仓库根** 展开 |
| 环境变量 | `${FACTORY_CODE_ROOT}/java` | 展开后按上两类处理 |

**约束：**

- 解析后的绝对路径 **不得** 位于 `multi-agent-code-factory` 仓库根之下（否则 Profile 加载失败）。
- 目录不存在时，Developer 首次写入前由引擎 **创建**（或 run 启动时 `mkdir -p`，实现择一）。
- `run_meta.json` 的 `profile.code_root` 存 **解析后的绝对路径**（审计与 resume）。
- CLI `--code-root <path>` 可单次覆盖 Profile 默认值（P1）。

**内置 Profile 示例：**

| Profile | `code_root`（YAML） | 典型用途 |
|---------|---------------------|----------|
| `python` | `../generated/python` | Python Todo 等 |
| `go` | `../generated/go` | Go CLI 示例 |
| `java` | `../generated/java` | Java Maven 示例 |
| `rust` | `../generated/rust` | Rust CLI 示例 |
| `solidity` | `../generated/solidity` | Foundry 合约示例 |

**Tool 约定：** `read_file` / `write_file` / `run_tests` / `linter` 的路径均相对 **解析后的 `code_root`**；`hitl.sensitive_globs` 同理。

---

## 2. Toolchain（语言无关 Test 层）

```text
run_tests Tool：setup（可选）→ build（可选）→ test_command → test_parser → TestReport
```

| `toolchain` 字段 | 说明 |
|------------------|------|
| `setup` | 跑测前准备（`go mod tidy`、`mvn compile`、`forge build` 等） |
| `build` | 可选编译步骤 |
| `test_command` | QA 节点执行的 shell 命令（**必须**） |
| `test_parser` | Parser 插件 id → 归一化为 `TestReport` |
| `test_artifacts` | Parser 读取的文件（如 JUnit XML） |
| `lint_command` | Developer / Reviewer 可选；Python 见 [python-style.md](./python-style.md) |
| `test_dir_glob` | 测试文件 glob；`tests_missing` 检测与 Architect 参考 |

### Parser 插件

实现：`multi_agent_code_factory/tools/test_parsers/`

| `test_parser` | 适用 | 输入 |
|---------------|------|------|
| `junit_xml` | Python（pytest）、Java（Maven/Gradle）、Hardhat | JUnit XML |
| `go_json` | Go | `go test -json` stdout |
| `cargo_json` | Rust | `cargo test --message-format=json` stdout |
| `forge_json` | Solidity（Foundry） | `forge test --json` stdout |
| `exit_code_only` | 兜底 | `exit_code` + stderr 尾部 |

详见 [test-report.md](./artifact-schemas/test-report-spec.md)。

---

## 3. Profile 矩阵（V1）

| Profile id | 文件 | `language` | 构建 / 测试 | Parser |
|------------|------|------------|-------------|--------|
| `python` | [python.yaml](../../../multi_agent_code_factory/profiles/python.yaml) | python | pip / pytest | `junit_xml` |
| `go` | [go.yaml](../../../multi_agent_code_factory/profiles/go.yaml) | go | go test -json | `go_json` |
| `java` | [java.yaml](../../../multi_agent_code_factory/profiles/java.yaml) | java | Maven | `junit_xml` |
| `rust` | [rust.yaml](../../../multi_agent_code_factory/profiles/rust.yaml) | rust | Cargo | `cargo_json` |
| `solidity` | [solidity.yaml](../../../multi_agent_code_factory/profiles/solidity.yaml) | solidity | Foundry | `forge_json` |

**P2（文档预留，尚无 YAML）：** `java-gradle`、`solidity-hardhat` 等变体 Profile。

**角色 prompt：** PM / Architect / Reviewer 共用 [`profiles/_shared/prompts/`](../../../multi_agent_code_factory/profiles/_shared/prompts/)；Developer 使用各语言 `profiles/<language>/prompts/developer.txt` 与 `{language}-style-snippet.txt`。

---

## 4. 语言约定（摘要）

### 编码规范（两层）

| 层 | 文档 / 文件 | 注入 |
|----|-------------|------|
| **通用** | [dev-principles-spec.md](./artifact-templates/dev-principles-spec.md) | `profiles/_shared/prompts/developer-principles-snippet.txt`（Developer） |
| **语言** | `{language}-style-snippet.txt`；Python 详见 [python-style.md](./python-style.md) | Developer，在通用 snippet 之后 |

### 编码规范 snippet（各语言）

- 路径：`profiles/<language>/prompts/{language}-style-snippet.txt`（可选别名 `style-snippet.txt`）。
- 注入：**Developer** 节点依次注入 `developer-principles-snippet.txt` + 语言 snippet；PM / Architect 等不注入。
- 解析：`agents/llm/prompt/style_snippet.py` · `load_dev_principles_snippet()`。

### Python（`python`）

- 规范：[python-style.md](./python-style.md)；工具配置：仓库根 `pyproject.toml`。
- Lint：`python -m ruff check . && python -m ruff format --check .`；测试：`python -m pytest` + `junit_xml` Parser。
- Snippet：`profiles/python/prompts/python-style-snippet.txt`。

### Go（`go`）

- Lint：`golangci-lint run ./...`；测试：`go test -json ./...`。
- Snippet：`profiles/go/prompts/go-style-snippet.txt`；Developer：`developer.txt`。

### Java（Maven）

- 布局：`src/main/java`、`src/test/java`；测试类 `*Test.java`；JUnit 5 + Surefire。
- Lint：`mvn -q checkstyle:check`；测试：`mvn -q test`。
- Snippet：`profiles/java/prompts/java-style-snippet.txt`；Developer：`developer.txt`.
- Gradle 在 Windows 上 `./gradlew` 可由 `profiles.py` 归一为 `gradlew.bat`（P2）。

### Rust（Cargo）

- 单元测试：`src/**/*.rs` 内 `#[cfg(test)]`；集成测试：`tests/*.rs`。
- Lint：`cargo clippy --all-targets --all-features -- -D warnings`；测试：`cargo test --message-format=json`.
- Snippet：`profiles/rust/prompts/rust-style-snippet.txt`；Developer：`developer.txt`.
- P2 可选 [cargo-nextest](https://nexte.st/) + `junit_xml` Parser。

### Solidity（Foundry，推荐）

- 合约 `src/*.sol`；测试 `test/*.t.sol`；`forge-std`。
- Lint：`forge fmt --check`；测试：`forge test --json`.
- Snippet：`profiles/solidity/prompts/solidity-style-snippet.txt`；Developer：`developer.txt`.
- **禁止** QA 连主网 RPC；`script/`、`broadcast/` 变更触发 HITL。

### Solidity（Hardhat，P2）

- 合约 `contracts/*.sol`；测试 TS/JS；需 `mocha-junit-reporter`。

---

## 5. 运行示例

```bash
python -m multi_agent_code_factory run --profile python --task-id todo-cli "实现命令行 Todo"
python -m multi_agent_code_factory run --profile java --task-id order-api "实现订单 REST API"
python -m multi_agent_code_factory run --profile rust --task-id todo-rs "实现 Rust CLI Todo"
python -m multi_agent_code_factory run --profile solidity --task-id vault "实现 ERC4626 金库与测试"
```

---

## 6. V2 领域 Profile（暂不验收）

领域 Profile 与配套设计见 [domains/](../../../domains/README.md)（如 [domains/arb/](../../../domains/arb/)）。
