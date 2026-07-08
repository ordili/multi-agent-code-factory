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
        output_schema: type[T],
        system_prompt: str,
        user_prompt: str,
    ) -> InvokeResult[T]:
        """调用 LLM 一次并解析为 ``InvokeResult``。

        Args:
            model: LangChain ``BaseChatModel``；默认由 ``create_chat_model()``
                创建（``init_chat_model``，按 ``FACTORY_LLM_PROVIDER`` 解析）。
            role_id: 发起调用的 Agent 角色，用于日志与错误信息。
            output_schema: 期望输出的 Pydantic 模型类（如 ``ArchitectLLMOutput``）。
            system_prompt: 组装好的 system 消息
                （角色 prompt、风格 snippet、可选 JSON 规则）。
            user_prompt: 组装好的 user 消息（通常为 JSON 序列化后的推理上下文）。
        """
        ...
