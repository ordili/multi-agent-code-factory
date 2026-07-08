"""从 LangChain 响应提取 token 用量。"""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.agents.llm.usage.models import TokenUsage


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def _usage_from_mapping(data: dict[str, Any]) -> TokenUsage:
    prompt = _coerce_int(
        data.get("input_tokens")
        or data.get("prompt_tokens")
        or data.get("prompt_eval_count")
    )
    completion = _coerce_int(
        data.get("output_tokens")
        or data.get("completion_tokens")
        or data.get("eval_count")
    )
    total = _coerce_int(data.get("total_tokens"))
    if total is None and prompt is not None and completion is not None:
        total = prompt + completion
    return TokenUsage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=total,
    )


def extract_token_usage(response: Any) -> TokenUsage:
    """从 LangChain AIMessage 或类似响应对象读取 token 计数。"""
    usage_meta = getattr(response, "usage_metadata", None)
    if isinstance(usage_meta, dict) and usage_meta:
        extracted = _usage_from_mapping(usage_meta)
        if extracted.resolved_total() > 0:
            return extracted

    response_meta = getattr(response, "response_metadata", None)
    if isinstance(response_meta, dict):
        token_usage = response_meta.get("token_usage")
        if isinstance(token_usage, dict) and token_usage:
            extracted = _usage_from_mapping(token_usage)
            if extracted.resolved_total() > 0:
                return extracted
        extracted = _usage_from_mapping(response_meta)
        if extracted.resolved_total() > 0:
            return extracted

    return TokenUsage()
