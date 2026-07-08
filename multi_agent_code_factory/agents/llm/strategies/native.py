"""LangChain native structured output strategy."""

from __future__ import annotations

from typing import Any, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.types import InvokeResult

T = TypeVar("T", bound=BaseModel)


class NativeStructuredStrategy:
    """Use LangChain ``with_structured_output``."""

    def invoke(
        self,
        model: Any,
        *,
        role_id: AgentRole,
        schema: type[T],
        system_prompt: str,
        user_prompt: str,
    ) -> InvokeResult[T]:
        del role_id
        structured = model.with_structured_output(schema, include_raw=True)
        payload = structured.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        raw: Any | None = None
        if isinstance(payload, dict):
            raw = payload.get("raw")
            parsed = payload.get("parsed")
        else:
            parsed = payload
        if not isinstance(parsed, schema):
            parsed = schema.model_validate(parsed)
        return InvokeResult(parsed=parsed, raw_response=raw)
