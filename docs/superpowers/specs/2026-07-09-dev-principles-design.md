# Dev Principles — 设计说明

> **日期：** 2026-07-09  
> **状态：** 已定稿  
> **关联规范：** [`artifact-templates/dev-principles-spec.md`](../../design/pipeline/artifact-templates/dev-principles-spec.md)

## 背景

`artifact-templates/` 原先只覆盖 PM / Architect / Reviewer 的人读产物格式，缺少 **Developer 写代码应遵循的跨语言工程原则**（如 `README.md`、单一职责）。语言相关规范分散在 `python-style.md` 与各 `{language}-style-snippet.txt`。

## 决策

采用 **两层分离（方案 A + 方案 1）**：

| 层 | 文档 / 注入 | 内容 |
|----|-------------|------|
| **通用** | `dev-principles-spec.md` + `_shared/prompts/dev-principles-snippet.txt` | README、SRP、测试纪律、安全卫生 |
| **语言** | `{language}-style-snippet.txt` + `python-style.md` 等 | PEP8、Ruff、pytest、go test 等 |

## 运行时

Developer system prompt 组装顺序：

```text
developer.txt → dev-principles-snippet.txt → {language}-style-snippet.txt
```

实现：`agents/llm/prompt/builder.py` + `load_dev_principles_snippet()`。

## 边界

- **不新增** `artifact-schemas` JSON 契约；DevManifest 仍仅 JSON。
- **V1 不做** quality-gates 强制校验 README 存在。
- Reviewer 在 `review-spec.md` 文档级引用 dev-principles，不强制改 Reviewer prompt。

## 同步更新

- `artifact-templates/README.md`、`artifact-schemas/README.md`
- `profiles.md` §编码规范
- `python-style.md` 去重并引用 dev-principles
