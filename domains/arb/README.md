# 套利领域（V2）

> **不在 V1 范围。** Profile 与文档均在本目录，不作为当前里程碑验收项。

| 路径 | 内容 |
|------|------|
| [profile/arb.yaml](./profile/arb.yaml) | 套利 Profile（以该 YAML 为准） |
| [profile/prompts/](./profile/prompts/) | 领域 prompt（当前仅 style snippet） |
| [design/arb-factory-design.md](./design/arb-factory-design.md) | 工厂侧：HITL、Profile 约束 |
| [design/arb-core-design.md](./design/arb-core-design.md) | 运行时与 PROD 部署 |

**生成代码根（仓库外）：** `../arb-robot/`（由 `profile/arb.yaml` 的 `code_root` 指定）

## V2 待办（arb）

| 状态 | 项 | 说明 |
|------|-----|------|
| [ ] | 引擎加载 `domains/arb/profile/arb.yaml` | 依赖 [domains/README.md](../README.md) 全局项 |
| [ ] | `profile/prompts/developer.txt` | Live Developer 必需；当前缺失会 fallback 通用一行 |
| [x] | `profile/prompts/python-style-snippet.txt` | 已有；接入引擎后与 V1 Python 路径一致 |
| [ ] | 可选：领域覆盖 `pm.txt` / `architect.txt` | 默认复用 `profiles/_shared/prompts/` |
| [ ] | arb **Live e2e**（`require_hitl: true` 流程） | 设计见 `design/arb-factory-design.md` |

## 与 V1 共享机制

- **PM / Architect / Reviewer**：无需在本目录重复 prompt；引擎 `load_role_prompt` 会回退到 `profiles/_shared/prompts/`。
- **Developer**：须在本目录或继承语言 Profile 提供 `developer.txt`；style snippet 文件名须与 `profile.language` 一致（当前为 `python` → `python-style-snippet.txt`）。
