"""调用策略协议（Protocol）。

工厂 Live 模式的业务场景统一为：多 Agent **强推理** + 结构化产物（Pydantic schema）。
各策略的差异在于 **如何让模型输出符合 schema**，而非是否为「闲聊」：

- ``native_structured`` → openai、anthropic（API 原生 structured output）
- ``prompted_json`` → deepseek、ollama（提示词 JSON 约束 + 本地解析）

权威 provider 列表见 ``strategies/modes.py``。
"""

from __future__ import annotations

from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.types import InvokeResult

T = TypeVar("T", bound=BaseModel)


class InvokeStrategy(Protocol[T]):
    """调用 LLM 并解析为结构化输出。"""

    def invoke(
        self,
        model: Any,
        *,
        role_id: AgentRole,
        schema: type[T],
        system_prompt: str,
        user_prompt: str,
    ) -> InvokeResult[T]: ...
