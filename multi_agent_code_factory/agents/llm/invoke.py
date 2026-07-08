"""LLM 调用与结构化 JSON 解析（LangChain structured / prompted JSON）。"""

from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.base import (
    default_stub_fixtures,
    load_json_fixture,
)
from multi_agent_code_factory.llm import LlmInvokeError

T = TypeVar("T", bound=BaseModel)

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)

_TRANSIENT_ERROR_NAMES = frozenset(
    {
        "ResponseError",
        "ReadError",
        "RemoteProtocolError",
        "ConnectionError",
        "TimeoutError",
    }
)

PROMPTED_JSON_PROVIDERS = frozenset({"ollama", "deepseek"})


def extract_json_text(raw: str) -> str:
    """去除模型输出中的 markdown 围栏与首尾空白。"""
    text = raw.strip()
    if text.startswith("```"):
        text = _JSON_FENCE_RE.sub("", text).strip()
    return text


def uses_prompted_json(provider: str) -> bool:
    """不支持 LangChain ``with_structured_output`` 的 provider 需走提示词 JSON 模式。"""
    return provider in PROMPTED_JSON_PROVIDERS


def is_transient_llm_error(exc: BaseException) -> bool:
    """判断异常是否为可重试的瞬态 LLM/网络错误。"""
    name = type(exc).__name__
    if name in _TRANSIENT_ERROR_NAMES:
        return True
    message = str(exc).lower()
    return "502" in message or "503" in message or "connection" in message


def ollama_invoke_hint(model: str) -> str:
    """构造 Ollama/DeepSeek 调用失败时的排查提示信息。"""
    return (
        f"LLM call failed for model {model!r}. "
        "For Ollama: restart the server and prefer qwen3.5:9b for large JSON specs. "
        "For DeepSeek: use deepseek-chat or deepseek-v4-pro with prompted JSON mode. "
        "Or switch FACTORY_LLM_PROVIDER=ollama."
    )


def example_json_for_schema(schema: type[BaseModel]) -> str | None:
    """为 prompted JSON 模式提供 stub fixture 示例，帮助模型对齐输出形状。"""
    fixtures = default_stub_fixtures()
    mapping: dict[str, Any] = {
        "SpecArtifact": fixtures.spec,
        "DesignArtifact": fixtures.design,
    }
    path = mapping.get(schema.__name__)
    if path is None:
        return None
    return json.dumps(load_json_fixture(path), ensure_ascii=False, indent=2)


def invoke_langchain_structured(
    model: Any,
    *,
    schema: type[T],
    system_prompt: str,
    user_prompt: str,
) -> tuple[T, Any | None]:
    """通过 LangChain ``with_structured_output`` 调用并解析为 Pydantic 模型。"""
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
    return parsed, raw


def invoke_prompted_json(
    model: Any,
    *,
    role_id: AgentRole,
    schema: type[T],
    system_prompt: str,
    user_prompt: str,
) -> tuple[T, Any]:
    """Ollama/DeepSeek 路径：提示词约束 JSON 输出，再手动 ``json.loads`` + 校验。"""
    example = example_json_for_schema(schema)
    json_rules = (
        "Output ONLY one JSON object. No markdown fences, no commentary.\n"
        "Match field names and nested object shapes exactly."
    )
    if example:
        json_rules += f"\n\nExample JSON shape:\n{example}"
    else:
        json_rules += (
            f"\n\nJSON schema (follow types strictly):\n"
            f"{json.dumps(schema.model_json_schema(), ensure_ascii=False, indent=2)}"
        )
    messages = [
        SystemMessage(content=f"{system_prompt}\n\n{json_rules}"),
        HumanMessage(content=user_prompt),
    ]
    response = model.invoke(messages)
    content = getattr(response, "content", response)
    if not isinstance(content, str) or not content.strip():
        msg = f"Ollama returned empty content for role={role_id} schema={schema.__name__}"
        raise LlmInvokeError(msg)
    try:
        payload = json.loads(extract_json_text(content))
    except json.JSONDecodeError as exc:
        msg = (
            f"Ollama JSON parse failed for role={role_id} schema={schema.__name__}: {exc}\n"
            f"Raw output (first 800 chars): {content[:800]}"
        )
        raise LlmInvokeError(msg) from exc
    try:
        return schema.model_validate(payload), response
    except ValidationError as exc:
        msg = f"Ollama JSON did not match schema {schema.__name__} for role={role_id}: {exc}"
        raise LlmInvokeError(msg) from exc
