"""LLM 预算检查与 run_meta 累计。"""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.agents.llm.budget.errors import LlmBudgetExceededError

__all__ = [
    "LlmBudgetExceededError",
    "check_llm_budget",
    "record_llm_call",
    "resolved_call_tokens",
]


def __getattr__(name: str) -> Any:
    if name == "check_llm_budget":
        from multi_agent_code_factory.agents.llm.budget.guard import check_llm_budget

        return check_llm_budget
    if name == "record_llm_call":
        from multi_agent_code_factory.agents.llm.budget.ledger import record_llm_call

        return record_llm_call
    if name == "resolved_call_tokens":
        from multi_agent_code_factory.agents.llm.budget.ledger import (
            resolved_call_tokens,
        )

        return resolved_call_tokens
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
