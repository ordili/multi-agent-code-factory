"""调用前 LLM 预算检查。"""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.agents.llm.budget.errors import LlmBudgetExceededError
from multi_agent_code_factory.config import FactoryConfig


def check_llm_budget(
    writer: Any,
    factory_config: FactoryConfig | None,
) -> None:
    """调用前检查 run_meta 中的 LLM 次数/token 预算。"""
    if factory_config is None or factory_config.budget is None:
        return
    meta = writer.read_meta()
    if meta is None or meta.budget is None:
        return
    budget = meta.budget
    max_calls = budget.max_llm_calls
    used_calls = budget.used_llm_calls or 0
    if max_calls is not None and used_calls >= max_calls:
        msg = f"LLM call budget exceeded ({used_calls}/{max_calls})"
        raise LlmBudgetExceededError(msg)
    max_tokens = budget.max_tokens
    used_tokens = budget.used_tokens or 0
    if max_tokens is not None and used_tokens >= max_tokens:
        msg = f"LLM token budget exceeded ({used_tokens}/{max_tokens})"
        raise LlmBudgetExceededError(msg)
