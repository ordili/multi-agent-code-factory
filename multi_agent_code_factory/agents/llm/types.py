"""Structured LLM invoke request/result types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from multi_agent_code_factory.agent_roles import AgentRole

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class InvokeRequest(Generic[T]):
    """One structured LLM call."""

    role_id: AgentRole
    schema: type[T]
    context: dict[str, Any]
    extra_system: str | None = None


@dataclass(frozen=True)
class InvokeResult(Generic[T]):
    """Parsed schema plus raw provider response for usage extraction."""

    parsed: T
    raw_response: Any | None
