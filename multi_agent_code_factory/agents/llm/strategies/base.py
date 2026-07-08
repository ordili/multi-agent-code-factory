"""Invoke strategy protocol."""

from __future__ import annotations

from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.types import InvokeResult

T = TypeVar("T", bound=BaseModel)


class InvokeStrategy(Protocol[T]):
    """Call an LLM and parse structured output."""

    def invoke(
        self,
        model: Any,
        *,
        role_id: AgentRole,
        schema: type[T],
        system_prompt: str,
        user_prompt: str,
    ) -> InvokeResult[T]: ...
