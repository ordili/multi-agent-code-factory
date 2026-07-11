"""Tests for LlmPromptShape helper."""

from __future__ import annotations

from multi_agent_code_factory.schemas.llm_prompt_shape import (
    LlmPromptShape,
    prompt_shape_for_schema,
)
from multi_agent_code_factory.schemas.prd import PrdArtifact


def test_prompt_shape_for_schema_returns_llm_prompt_shape() -> None:
    shape = prompt_shape_for_schema(PrdArtifact)
    assert shape is not None
    assert shape.json_shape["title"] == "CLI Todo App"
    assert shape.notes is None


def test_llm_prompt_shape_is_frozen() -> None:
    shape = LlmPromptShape(json_shape={"a": 1})
    try:
        shape.json_shape = {"b": 2}  # type: ignore[misc]
        raised = False
    except AttributeError:
        raised = True
    assert raised
