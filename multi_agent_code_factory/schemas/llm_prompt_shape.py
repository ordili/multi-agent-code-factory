"""prompted_json 用 JSON 形状示范（非 Run 产物、非 JSON Schema examples）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Protocol, runtime_checkable

from pydantic import BaseModel


@dataclass(frozen=True, slots=True)
class LlmPromptShape:
    """LLM few-shot 示例载荷：字段嵌套形状 + 可选补充说明。"""

    json_shape: dict[str, Any]
    notes: str | None = None


@runtime_checkable
class HasLlmPromptShape(Protocol):
    """声明 ``LLM_PROMPT_SHAPE`` 的 Pydantic 模型。"""

    LLM_PROMPT_SHAPE: ClassVar[LlmPromptShape]


def prompt_shape_for_schema(schema: type[BaseModel]) -> LlmPromptShape | None:
    """读取 schema 类上的 ``LLM_PROMPT_SHAPE``。"""
    shape = getattr(schema, "LLM_PROMPT_SHAPE", None)
    if isinstance(shape, LlmPromptShape):
        return shape
    return None
