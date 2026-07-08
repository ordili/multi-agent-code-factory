"""Live 模式 LLM 调用子包。"""

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
from multi_agent_code_factory.agents.llm.budget.errors import LlmBudgetExceededError
from multi_agent_code_factory.llm import LlmInvokeError, provider_spec


def uses_prompted_json(provider: str) -> bool:
    """deepseek/ollama 为 True（``output_mode=prompted_json``），其余为 False。"""
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
