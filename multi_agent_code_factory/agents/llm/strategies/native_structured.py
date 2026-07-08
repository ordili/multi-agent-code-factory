"""LangChain 原生 structured output 调用策略。

当 ``LlmRuntimeConfig.output_mode == "native_structured"`` 时使用。

支持的 ``FACTORY_LLM_PROVIDER``（见 ``modes.NATIVE_STRUCTURED_PROVIDERS``）：
openai、anthropic。

适用场景：与 prompted_json 相同——工厂 Live 多 Agent **强推理**与结构化产物输出；
本路径通过 API 原生 structured output 完成 schema 约束。

机制：LangChain ``with_structured_output`` 将 JSON 结构约束交给厂商 API
（tool / function calling），本路径不做手动 ``json.loads``。
"""

from __future__ import annotations

from typing import Any, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.strategies.modes import (
    NATIVE_STRUCTURED_PROVIDERS,
)
from multi_agent_code_factory.agents.llm.types import InvokeResult

T = TypeVar("T", bound=BaseModel)

# 供文档/测试从策略模块导入 provider 列表
SUPPORTED_PROVIDERS = NATIVE_STRUCTURED_PROVIDERS


class NativeStructuredStrategy:
    """强推理场景下通过 LangChain ``with_structured_output`` 调用。"""

    output_mode = "native_structured"
    supported_providers = SUPPORTED_PROVIDERS

    def invoke(
        self,
        model: Any,
        *,
        role_id: AgentRole,
        output_schema: type[T],
        system_prompt: str,
        user_prompt: str,
    ) -> InvokeResult[T]:
        del role_id
        structured = model.with_structured_output(output_schema, include_raw=True)
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
        if not isinstance(parsed, output_schema):
            parsed = output_schema.model_validate(parsed)
        return InvokeResult(parsed=parsed, raw_response=raw)
