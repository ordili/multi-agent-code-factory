# Profile 配置

每个 **语言** 一个可加载 Profile（`python`、`go`、`java`、`rust`、`solidity`）；公共字段在 `_base/common.yaml`，经 `extends` 合并。字段说明见 [docs/design/pipeline/profiles.md](../../docs/design/pipeline/profiles.md)。

## 如何选择语言

`run --profile <id>` **必填**（无默认，不从需求推断）。`--profile` 选的是**语言栈配置**（含测试命令与 prompts）；**V1 下 id 与语言同名**。首次推荐 **`python`**。

Profile 是语言栈；具体项目用 `--task-id` + `--code-root` 区分，不是换 Profile id。

## Profile 与 `.env` 的分工

| 放 **Profile**（本目录 YAML） | 放 **`.env`**（仓库根，不进 Git） |
|------------------------------|-----------------------------------|
| 语言、`toolchain`、测试/ lint 命令 | 厂商 API Key（`DEEPSEEK_API_KEY` 等，未用留空） |
| `validation`、`hitl`、角色 prompts | `FACTORY_LLM_PROVIDER`、`FACTORY_LLM_MODEL` |
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
└── python/prompts/         # 按语言放 prompt；编码规范为 {language}-style-snippet.txt
```

各语言 **Developer** Live 模式需具备：

- `{language}/prompts/developer.txt` — 角色任务说明（语言相关）
- `{language}/prompts/{language}-style-snippet.txt` — 语言编码规范（Developer 注入，在通用原则之后）

**所有语言 Developer** 另注入 `_shared/prompts/developer-principles-snippet.txt`（README、SRP 等；见 [dev-principles-spec.md](../../docs/design/pipeline/artifact-templates/dev-principles-spec.md)）。

**PM / Architect / Reviewer** 与语言无关，共用 `profiles/_shared/prompts/{role}.txt`（产出 Spec / Design / Review JSON 或 Mermaid）。各语言目录可放 `{role}.txt` 覆盖共享版。

当前状态：

| 角色 | 共享 prompt | 语言专用 |
|------|-------------|----------|
| PM | `_shared/prompts/pm.txt` | — |
| Architect | `_shared/prompts/architect.txt` | — |
| Reviewer | `_shared/prompts/reviewer.txt` | — |
| Developer | `_shared/prompts/developer-principles-snippet.txt` | 各语言 `developer.txt` + `{language}-style-snippet.txt` |

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
