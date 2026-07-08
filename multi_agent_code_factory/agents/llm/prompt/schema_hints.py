"""JSON output instructions for prompted-json providers."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel


def llm_example_for_schema(schema: type[BaseModel]) -> dict[str, Any] | None:
    """Return compact example JSON from ``schema.__llm_example__`` when present."""
    example = getattr(schema, "__llm_example__", None)
    if isinstance(example, dict):
        return example
    return None


def json_output_instructions(schema: type[BaseModel]) -> str:
    """Instructions appended to system prompt for prompted JSON mode."""
    rules = (
        "Output ONLY one JSON object. No markdown fences, no commentary.\n"
        "Match field names and nested object shapes exactly."
    )
    example = llm_example_for_schema(schema)
    if example is not None:
        return f"{rules}\n\nExample JSON shape:\n{json.dumps(example, ensure_ascii=False, indent=2)}"
    return (
        f"{rules}\n\nJSON schema (follow types strictly):\n"
        f"{json.dumps(schema.model_json_schema(), ensure_ascii=False, indent=2)}"
    )
