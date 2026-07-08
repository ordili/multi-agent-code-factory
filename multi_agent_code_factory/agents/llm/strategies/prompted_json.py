"""Prompted JSON invoke strategy for providers without native structured output."""

from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.errors import LlmParseError
from multi_agent_code_factory.agents.llm.prompt.schema_hints import json_output_instructions
from multi_agent_code_factory.agents.llm.types import InvokeResult
from multi_agent_code_factory.llm import LlmInvokeError

T = TypeVar("T", bound=BaseModel)

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def extract_json_text(raw: str) -> str:
    """Strip markdown fences and surrounding whitespace from model output."""
    text = raw.strip()
    if text.startswith("```"):
        text = _JSON_FENCE_RE.sub("", text).strip()
    return text


class PromptedJsonStrategy:
    """Append JSON rules to system prompt, then parse and validate manually."""

    def invoke(
        self,
        model: Any,
        *,
        role_id: AgentRole,
        schema: type[T],
        system_prompt: str,
        user_prompt: str,
    ) -> InvokeResult[T]:
        json_rules = json_output_instructions(schema)
        messages = [
            SystemMessage(content=f"{system_prompt}\n\n{json_rules}"),
            HumanMessage(content=user_prompt),
        ]
        response = model.invoke(messages)
        content = getattr(response, "content", response)
        if not isinstance(content, str) or not content.strip():
            msg = (
                f"LLM returned empty content for role={role_id} "
                f"schema={schema.__name__}"
            )
            raise LlmInvokeError(msg)
        try:
            payload = json.loads(extract_json_text(content))
        except json.JSONDecodeError as exc:
            msg = (
                f"JSON parse failed for role={role_id} schema={schema.__name__}: {exc}\n"
                f"Raw output (first 800 chars): {content[:800]}"
            )
            raise LlmParseError(msg) from exc
        try:
            parsed = schema.model_validate(payload)
        except ValidationError as exc:
            msg = (
                f"JSON did not match schema {schema.__name__} "
                f"for role={role_id}: {exc}"
            )
            raise LlmParseError(msg) from exc
        return InvokeResult(parsed=parsed, raw_response=response)
