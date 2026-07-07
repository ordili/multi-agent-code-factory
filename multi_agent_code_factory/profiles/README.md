# Profile 配置

每个 **语言** 一个可加载 Profile（`python`、`go`、`java`、`rust`、`solidity`）；公共字段在 `_base/common.yaml`，经 `extends` 合并。字段说明见 [docs/design/pipeline/profiles.md](../../docs/design/pipeline/profiles.md)。

## Profile 与 `.env` 的分工

| 放 **Profile**（本目录 YAML） | 放 **`.env`**（仓库根，不进 Git） |
|------------------------------|-----------------------------------|
| 语言、`toolchain`、测试/ lint 命令 | `DEEPSEEK_API_KEY` 等 LLM 密钥 |
| `validation`、`hitl`、角色 prompts | 本机可选：`DEEPSEEK_MODEL`、`FACTORY_CHAT_MODEL` |
| `code_root` 路径**约定**（如 `../generated/python`） | 仅当 YAML 用 `${FACTORY_CODE_ROOT}/…` 时，在此设 `FACTORY_CODE_ROOT` |
| `tools` 列表 | 可选：覆盖 `FACTORY_MAX_*` 回路上限 |

**具体项目**（计算器、Todo）不是 Profile：用 `--profile python` + `--code-root ../generated/<project>` + `--task-id`。

详见 [profiles.md §0](../../docs/design/pipeline/profiles.md#0-配置分层profile-vs-env-vs-其它)。

## 目录约定

```text
profiles/
├── _base/common.yaml       # 公共默认（不可 --profile）
├── python.yaml             # extends common
├── go.yaml / java.yaml / …
└── python/prompts/         # 按语言放 prompt（python 已有完整集）
```

## V1 语言 Profile

| 文件 | id | language | 说明 |
|------|-----|----------|------|
| `python.yaml` | python | python | MVP；pytest + JUnit XML |
| `go.yaml` | go | go | P1 |
| `java.yaml` | java | java | P1；默认 Maven |
| `rust.yaml` | rust | rust | P1 |
| `solidity.yaml` | solidity | solidity | P1；默认 Foundry |

## V2 领域 Profile

领域 Profile 位于仓库根 [`domains/`](../../domains/README.md)，**不纳入 V1 加载路径与验收**。

新增语言 Profile：在 `_base/common.yaml` 上 `extends`，改 `id`、`language`、`toolchain`、`code_root`，并登记 [profiles.md](../../docs/design/pipeline/profiles.md) 矩阵。
