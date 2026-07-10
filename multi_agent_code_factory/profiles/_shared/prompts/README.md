# `_shared/prompts`

语言无关的 LLM system prompt。组装见 `agents/llm/prompt/builder.py`。

## 各 Agent 使用的 System Prompt


| Agent     | 本目录                                               | Profile 目录（`profiles/{lang}/prompts/`）           |
| --------- | ------------------------------------------------- | ------------------------------------------------ |
| PM        | `pm.txt` + `artifact-language-snippet.txt`        | 可选 `pm.txt` 覆盖主 System Prompt                    |
| Architect | `architect.txt` + `artifact-language-snippet.txt` | 可选 `architect.txt` 覆盖                             |
| Reviewer  | `reviewer.txt` + `artifact-language-snippet.txt`  | 可选 `reviewer.txt` 覆盖                              |
| Developer | `developer-principles-snippet.txt`                | `developer.txt` + `{language}-style-snippet.txt` |
| QA 等      | —                                                 | —                                                |


调用时还会在 system 末尾追加 schema 的 JSON 示例（`json_output_instructions`，非本目录文件）。

## 本目录文件一览


| 文件                                          | 用于                                    |
| ------------------------------------------- | ------------------------------------- |
| `pm.txt` / `architect.txt` / `reviewer.txt` | 对应角色主 System Prompt |
| `artifact-language-snippet.txt`             | PM、Architect、Reviewer（产物叙述简体中文，id 英文） |
| `developer-principles-snippet.txt`          | Developer（README、SRP、测试、安全等）          |


