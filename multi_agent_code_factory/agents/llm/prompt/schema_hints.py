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


def json_output_instructions(schema: type[BaseModel]) -> str:
    """生成 appended 到 system prompt 的 JSON 输出指令（发给模型，保持英文）。"""
    rules = (
        "Output ONLY one JSON object. No markdown fences, no commentary.\n"
        "Match field names and nested object shapes exactly."
    )
    example = llm_example_for_schema(schema)
    if example is not None:
        example_json = json.dumps(example, ensure_ascii=False, indent=2)
        return f"{rules}\n\nExample JSON shape:\n{example_json}"
    return (
        f"{rules}\n\nJSON schema (follow types strictly):\n"
        f"{json.dumps(schema.model_json_schema(), ensure_ascii=False, indent=2)}"
    )
