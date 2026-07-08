"""Pre-invoke LLM budget guard."""

from __future__ import annotations

from multi_agent_code_factory.config import FactoryConfig
from multi_agent_code_factory.llm import LlmBudgetExceededError
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter


def check_llm_budget(
    writer: RunArtifactWriter,
    factory_config: FactoryConfig | None,
) -> None:
    """Check run_meta LLM call/token budget before invoking."""
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
