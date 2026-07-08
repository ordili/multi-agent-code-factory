"""从 LLM 响应提取 token 用量并汇总到 llm_usage 日志。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.schemas._base import ARTIFACT_VERSION


class TokenUsage(BaseModel):
    """单次 LLM 调用的 token 计数。"""

    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)

    def resolved_total(self) -> int:
        if self.total_tokens is not None:
            return self.total_tokens
        prompt = self.prompt_tokens or 0
        completion = self.completion_tokens or 0
        if prompt or completion:
            return prompt + completion
        return 0


class LlmCallUsage(BaseModel):
    """单次结构化 LLM 调用的用量记录。"""

    role_id: AgentRole
    schema_name: str
    attempt: int = Field(default=1, ge=1)
    duration_ms: int | None = Field(default=None, ge=0)
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class LlmUsageTotals(BaseModel):
    """run 内 LLM 调用的累计用量。"""

    llm_calls: int = Field(default=0, ge=0)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class LlmUsageLog(BaseModel):
    """写入 run 目录的 LLM 用量日志结构。"""

    version: ARTIFACT_VERSION
    provider: str
    model: str
    calls: list[LlmCallUsage] = Field(default_factory=list)
    totals: LlmUsageTotals = Field(default_factory=LlmUsageTotals)


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


def merge_usage_totals(
    current: LlmUsageTotals,
    call: LlmCallUsage,
) -> LlmUsageTotals:
    """将单次调用用量累加到 run 总计。"""
    prompt = call.prompt_tokens or 0
    completion = call.completion_tokens or 0
    total = call.total_tokens
    if total is None:
        total = prompt + completion
    return LlmUsageTotals(
        llm_calls=current.llm_calls + 1,
        prompt_tokens=current.prompt_tokens + prompt,
        completion_tokens=current.completion_tokens + completion,
        total_tokens=current.total_tokens + total,
    )
