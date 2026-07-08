"""提示词 JSON 调用策略（不走 API 原生 structured output 时使用）。

当 ``LlmRuntimeConfig.output_mode == "prompted_json"`` 时使用。

支持的 ``FACTORY_LLM_PROVIDER``（见 ``modes.PROMPTED_JSON_PROVIDERS``）：
deepseek、ollama。

适用场景：工厂 Live 模式下的多 Agent **强推理**链路（PM/Architect/Developer/Reviewer
根据上下文推理并输出 spec、design、code 等 **结构化产物**），不是普通闲聊。

机制：在已有角色 system prompt 与推理上下文之上追加 JSON 规则与 schema 示例，
调用 ``model.invoke``，再本地 ``json.loads`` + Pydantic 校验。
"""

from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.errors import LlmParseError
from multi_agent_code_factory.agents.llm.prompt.schema_hints import json_output_instructions
from multi_agent_code_factory.agents.llm.strategies.modes import PROMPTED_JSON_PROVIDERS
from multi_agent_code_factory.agents.llm.types import InvokeResult
from multi_agent_code_factory.llm import LlmInvokeError

T = TypeVar("T", bound=BaseModel)

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)

# 供文档/测试从策略模块导入 provider 列表
SUPPORTED_PROVIDERS = PROMPTED_JSON_PROVIDERS


def extract_json_text(raw: str) -> str:
    """去除模型输出中的 markdown 围栏与首尾空白。"""
    text = raw.strip()
    if text.startswith("```"):
        text = _JSON_FENCE_RE.sub("", text).strip()
    return text


class PromptedJsonStrategy:
    """强推理 + 提示词 JSON 约束 + 本地解析（deepseek、ollama）。""" 

    output_mode = "prompted_json"
    supported_providers = SUPPORTED_PROVIDERS

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
