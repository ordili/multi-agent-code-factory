"""LLM usage models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.schemas._base import ARTIFACT_VERSION


class TokenUsage(BaseModel):
    """Token counts for one LLM response."""

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
    """One structured LLM invoke audit record."""

    role_id: AgentRole
    schema_name: str
    attempt: int = Field(default=1, ge=1)
    duration_ms: int | None = Field(default=None, ge=0)
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    success: bool = True
    error_type: str | None = None


class LlmUsageTotals(BaseModel):
    """Aggregated LLM usage for one run."""

    llm_calls: int = Field(default=0, ge=0)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class LlmUsageLog(BaseModel):
    """Persisted ``llm_usage.json`` structure."""

    version: ARTIFACT_VERSION
    provider: str
    model: str
    calls: list[LlmCallUsage] = Field(default_factory=list)
    totals: LlmUsageTotals = Field(default_factory=LlmUsageTotals)


def merge_usage_totals(
    current: LlmUsageTotals,
    call: LlmCallUsage,
) -> LlmUsageTotals:
    """Add one call record to run totals."""
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
