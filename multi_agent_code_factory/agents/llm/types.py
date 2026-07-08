"""结构化 LLM 调用的请求/结果类型。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from multi_agent_code_factory.agent_roles import AgentRole

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class InvokeRequest(Generic[T]):
    """一次结构化 LLM 调用请求。"""

    role_id: AgentRole
    output_schema: type[T]
    context: dict[str, Any]
    extra_system: str | None = None


@dataclass(frozen=True)
class InvokeResult(Generic[T]):
    """解析后的 schema 与原始响应（用于提取 token 用量）。"""

    parsed: T
    raw_response: Any | None
