"""Live-mode LLM invoke package."""

from multi_agent_code_factory.agents.llm.errors import LlmParseError
from multi_agent_code_factory.agents.llm.runner import LlmRunner
from multi_agent_code_factory.agents.llm.schemas import (
    ArchitectLLMOutput,
    DeveloperLLMOutput,
    SourceFileWrite,
)
from multi_agent_code_factory.agents.llm.strategies.prompted_json import extract_json_text
from multi_agent_code_factory.agents.llm.usage import (
    LlmCallUsage,
    LlmUsageLog,
    LlmUsageTotals,
    TokenUsage,
    extract_token_usage,
    merge_usage_totals,
)
from multi_agent_code_factory.llm import LlmBudgetExceededError, LlmInvokeError, provider_spec


def uses_prompted_json(provider: str) -> bool:
    """Return True when provider uses prompted JSON instead of native structured output."""
    return provider_spec(provider).output_mode == "prompted_json"


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
