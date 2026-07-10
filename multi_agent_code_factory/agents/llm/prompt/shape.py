"""prompted_json LLM prompt 形状 re-export（定义在 ``schemas.llm_prompt_shape``）。"""

from multi_agent_code_factory.schemas.llm_prompt_shape import (
    HasLlmPromptShape,
    LlmPromptShape,
    prompt_shape_for_schema,
)

__all__ = [
    "HasLlmPromptShape",
    "LlmPromptShape",
    "prompt_shape_for_schema",
]
