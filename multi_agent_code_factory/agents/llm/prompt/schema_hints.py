"""prompted-json 模式的 JSON 输出指令。"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel


def llm_example_for_schema(schema: type[BaseModel]) -> dict[str, Any] | None:
    """从 schema 的 ``__llm_example__`` 读取紧凑 JSON 示例。"""
    example = getattr(schema, "__llm_example__", None)
    if isinstance(example, dict):
        return example
    return None


def llm_example_supplement_for_schema(schema: type[BaseModel]) -> str | None:
    """可选补充说明（如持久化场景的字段形态），避免主示例绑定单一业务。"""
    supplement = getattr(schema, "__llm_example_supplement__", None)
    if isinstance(supplement, str) and supplement.strip():
        return supplement.strip()
    return None


def json_output_instructions(schema: type[BaseModel]) -> str:
    """生成 appended 到 system prompt 的 JSON 输出指令（发给模型，保持英文）。"""
    rules = (
        "Output ONLY one JSON object. No markdown fences, no commentary.\n"
        "Match field names and nested object shapes exactly.\n"
        "The example shows field shapes only; derive names, paths, and counts "
        "from spec."
    )
    example = llm_example_for_schema(schema)
    if example is not None:
        example_json = json.dumps(example, ensure_ascii=False, indent=2)
        parts = [rules, f"Example JSON shape:\n{example_json}"]
        supplement = llm_example_supplement_for_schema(schema)
        if supplement is not None:
            parts.append(f"Optional supplement:\n{supplement}")
        return "\n\n".join(parts)
    return (
        f"{rules}\n\nJSON schema (follow types strictly):\n"
        f"{json.dumps(schema.model_json_schema(), ensure_ascii=False, indent=2)}"
    )
