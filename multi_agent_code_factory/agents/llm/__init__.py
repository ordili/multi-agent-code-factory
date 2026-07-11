"""Live 模式 LLM 调用子包。"""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.llm import LlmInvokeError, provider_spec

__all__ = [
    "ArchitectLLMOutput",
    "DeveloperLLMOutput",
    "LlmBudgetExceededError",
    "LlmCallUsage",
    "LlmInvokeError",
    "LlmParseError",
    "LlmRunner",
    "LlmUsageLog",
    "LlmUsageTotals",
    "SourceFileWrite",
    "TokenUsage",
    "extract_json_text",
    "extract_token_usage",
    "merge_usage_totals",
    "uses_prompted_json",
]


def uses_prompted_json(provider: str) -> bool:
    """deepseek/ollama 为 True（``output_mode=prompted_json``），其余为 False。"""
    return provider_spec(provider).output_mode == "prompted_json"


def __getattr__(name: str) -> Any:
    if name == "ArchitectLLMOutput":
        from multi_agent_code_factory.agents.llm.schemas import ArchitectLLMOutput

        return ArchitectLLMOutput
    if name == "DeveloperLLMOutput":
        from multi_agent_code_factory.agents.llm.schemas import DeveloperLLMOutput

        return DeveloperLLMOutput
    if name == "LlmBudgetExceededError":
        from multi_agent_code_factory.agents.llm.budget.errors import (
            LlmBudgetExceededError,
        )

        return LlmBudgetExceededError
    if name == "LlmCallUsage":
        from multi_agent_code_factory.agents.llm.usage.models import LlmCallUsage

        return LlmCallUsage
    if name == "LlmParseError":
        from multi_agent_code_factory.agents.llm.errors import LlmParseError

        return LlmParseError
    if name == "LlmRunner":
        from multi_agent_code_factory.agents.llm.runner import LlmRunner

        return LlmRunner
    if name == "LlmUsageLog":
        from multi_agent_code_factory.agents.llm.usage.models import LlmUsageLog

        return LlmUsageLog
    if name == "LlmUsageTotals":
        from multi_agent_code_factory.agents.llm.usage.models import LlmUsageTotals

        return LlmUsageTotals
    if name == "SourceFileWrite":
        from multi_agent_code_factory.agents.llm.schemas import SourceFileWrite

        return SourceFileWrite
    if name == "TokenUsage":
        from multi_agent_code_factory.agents.llm.usage.models import TokenUsage

        return TokenUsage
    if name == "extract_json_text":
        from multi_agent_code_factory.agents.llm.strategies.prompted_json import (
            extract_json_text,
        )

        return extract_json_text
    if name == "extract_token_usage":
        from multi_agent_code_factory.agents.llm.usage.extract import (
            extract_token_usage,
        )

        return extract_token_usage
    if name == "merge_usage_totals":
        from multi_agent_code_factory.agents.llm.usage.models import merge_usage_totals

        return merge_usage_totals
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
