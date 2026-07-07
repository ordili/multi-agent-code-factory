# Profile 配置

每个 Profile 一个 YAML 文件；**V1 真源**为本目录下的 `*.yaml`，说明文档见 [docs/design/pipeline/profiles.md](../../docs/design/pipeline/profiles.md)。Python Profile 另见 [python-style.md](../../docs/design/pipeline/python-style.md)。

| `gates` | 已废弃；使用 **`validation`** |

## V1 内置 Profile

| 文件 | id | language | 说明 |
|------|-----|----------|------|
| `default.yaml` | default | python | MVP；pytest + JUnit XML |
| `go-cli.yaml` | go-cli | go | P1 |
| `java-maven.yaml` | java-maven | java | P1 |
| `java-gradle.yaml` | java-gradle | java | P1 |
| `rust-cli.yaml` | rust-cli | rust | P1 |
| `solidity-foundry.yaml` | solidity-foundry | solidity | P1；推荐 |
| `solidity-hardhat.yaml` | solidity-hardhat | solidity | P2 |

## V2 领域 Profile

领域 Profile 位于仓库根 [`domains/`](../../domains/README.md)（如 [`domains/arb/profile/arb.yaml`](../../domains/arb/profile/arb.yaml)），**不纳入 V1 加载路径与验收**。

## 目录约定

```text
profiles/                    # V1 通用 Profile
├── <id>.yaml
└── <id>/prompts/

domains/<name>/profile/      # V2 领域 Profile
├── <id>.yaml
└── prompts/
```

新增 V1 Profile：复制最接近的 YAML，改 `id`、`code_root`（**须在 multi-agent-code-factory 仓库外**）、`toolchain`，并在 [profiles.md](../../docs/design/pipeline/profiles.md) 矩阵中登记。
