"""LLM 预算相关异常。"""

from __future__ import annotations

from multi_agent_code_factory.llm.types import LlmInvokeError


class LlmBudgetExceededError(LlmInvokeError):
    """Raised when run LLM call or token budget is exhausted."""
