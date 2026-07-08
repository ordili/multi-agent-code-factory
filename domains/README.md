# 领域包（V2）

> **V1 范围：** 仅 [docs/design/pipeline/](../docs/design/pipeline/multi-agent-pipeline-design.md) 中的 **通用** 多 Agent 流水线。  
> **本目录：** 各业务领域的 **Profile 配置、prompts 与设计文档**，与引擎代码分离，**不纳入 V1 实现与验收**。

| 子目录 | 说明 | 状态 |
|--------|------|------|
| [arb/](./arb/) | DEX↔DEX 套利（`profile/arb.yaml` + 设计 spec） | V2 草案 |

## V1 已就绪（V2 可复用，无需重复实现）

以下在 V1 已实现，领域 Profile 接入引擎后**直接生效**：

| 能力 | 落点 |
|------|------|
| PM / Architect / Reviewer 共享 prompt | `profiles/_shared/prompts/{pm,architect,reviewer}.txt` |
| Developer 编码规范 snippet（按 language） | `agents/llm/prompt/style_snippet.py` → `{language}-style-snippet.txt` |
| Developer 仅注入 style snippet | `agents/llm/prompt/builder.py` + `STYLE_SNIPPET_ROLES` |

领域包只需提供 **`profile/<id>.yaml`**、**`developer.txt`**（及可选 snippet / 角色覆盖），不必复制三份文档型 Agent prompt。

## V2 引擎待办（全局）

| 状态 | 项 | 落点 |
|------|-----|------|
| [ ] | `profiles.py` 扫描 `domains/*/profile/*.yaml` | `profiles.py`、`list_profile_ids` |
| [ ] | CLI `--profile <domain-id>` 可加载领域 Profile | `__main__.py` |
| [ ] | 领域 Profile **Live e2e** 验收 | `tests/integration/` |
| [ ] | 各语言完整规范文档（`go-style.md` 等） | `docs/design/pipeline/` |
| [ ] | Prompt Cache / 短期记忆（省 token） | 暂缓；[P1-backlog §9](../docs/design/pipeline/P1-backlog.md) |

## 目录约定

```text
domains/<name>/
├── README.md
├── profile/
│   ├── <id>.yaml
│   └── prompts/
│       ├── developer.txt          # 建议：语言/领域相关（必填 Live Developer）
│       ├── {language}-style-snippet.txt   # 可选；与 V1 命名一致
│       └── {role}.txt             # 可选；覆盖 profiles/_shared 中同 role
└── design/
    └── *.md
```

新增领域：在本目录下新建 `<name>/`，配套 `profile/<id>.yaml`；引擎加载 Profile 时须包含 `domains/*/profile/*.yaml`（**V2 实现**）。

## 子领域清单

| 领域 | README | 状态 |
|------|--------|------|
| arb | [arb/README.md](./arb/README.md) | 草案；见该文档 V2 checklist |
