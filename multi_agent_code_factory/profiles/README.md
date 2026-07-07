# Profile 配置

每个 Profile 一个 YAML 文件；**真源即本目录下的 `*.yaml`**，说明文档见 [docs/superpowers/specs/factory/profiles.md](../../docs/superpowers/specs/factory/profiles.md)。

| `gates` | 已废弃；使用 **`validation`** |

## 内置 Profile

| 文件 | id | language | 说明 |
|------|-----|----------|------|
| `default.yaml` | default | python | MVP；pytest + JUnit XML |
| `go-cli.yaml` | go-cli | go | P1 |
| `java-maven.yaml` | java-maven | java | P1 |
| `java-gradle.yaml` | java-gradle | java | P1 |
| `rust-cli.yaml` | rust-cli | rust | P1 |
| `solidity-foundry.yaml` | solidity-foundry | solidity | P1；推荐 |
| `solidity-hardhat.yaml` | solidity-hardhat | solidity | P2 |
| `arb.yaml` | arb | python | 套利；`code_root: ../arb-robot`（仓库外） |

## 目录约定

```text
profiles/
├── <id>.yaml              # Profile 配置
└── <id>/prompts/          # 该 Profile 的角色 prompt（可选）
```

新增 Profile：复制最接近的 YAML，改 `id`、`code_root`（**须在 multi-agent-code-factory 仓库外**）、`toolchain`，并在 `profiles.md` 矩阵中登记。
