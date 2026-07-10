"""prompted-json 模式的 JSON 输出指令。"""

from __future__ import annotations

import json

from pydantic import BaseModel

from multi_agent_code_factory.schemas.llm_prompt_shape import prompt_shape_for_schema


def json_output_instructions(schema: type[BaseModel]) -> str:
    """生成 appended 到 system prompt 的 JSON 输出指令（发给模型，保持英文）。"""
    rules = (
        "Output ONLY one JSON object. No markdown fences, no commentary.\n"
        "Match field names and nested object shapes exactly.\n"
        "The example shows field shapes only; derive names, paths, and counts "
        "from spec."
    )
    shape = prompt_shape_for_schema(schema)
    if shape is not None:
        example_json = json.dumps(shape.json_shape, ensure_ascii=False, indent=2)
        parts = [rules, f"Example JSON shape:\n{example_json}"]
        if shape.notes:
            parts.append(f"Optional supplement:\n{shape.notes}")
        return "\n\n".join(parts)
    return (
        f"{rules}\n\nJSON schema (follow types strictly):\n"
        f"{json.dumps(schema.model_json_schema(), ensure_ascii=False, indent=2)}"
    )
