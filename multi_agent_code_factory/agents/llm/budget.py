"""LLM 调用预算：调用前检查与 run_meta 累计。"""

from __future__ import annotations

from multi_agent_code_factory.agents.llm.usage import LlmCallUsage
from multi_agent_code_factory.config import FactoryConfig
from multi_agent_code_factory.schemas.run_meta import BudgetUsage
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter


def resolved_call_tokens(call: LlmCallUsage) -> int:
    """从单次调用记录中解析 token 总数（优先 total，否则 prompt + completion）。"""
    if call.total_tokens is not None:
        return call.total_tokens
    return (call.prompt_tokens or 0) + (call.completion_tokens or 0)


def check_llm_budget(
    writer: RunArtifactWriter,
    factory_config: FactoryConfig | None,
) -> None:
    """调用前检查 run_meta 中的 LLM 次数/token 预算，超限则抛 ``RuntimeError``。"""
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
        raise RuntimeError(msg)
    max_tokens = budget.max_tokens
    used_tokens = budget.used_tokens or 0
    if max_tokens is not None and used_tokens >= max_tokens:
        msg = f"LLM token budget exceeded ({used_tokens}/{max_tokens})"
        raise RuntimeError(msg)


def record_llm_call(
    writer: RunArtifactWriter,
    factory_config: FactoryConfig | None,
    call: LlmCallUsage,
) -> None:
    """将本次调用的次数与 token 累计写入 ``run_meta.json`` 的 budget 字段。"""
    meta = writer.read_meta()
    if meta is None:
        return
    budget = meta.budget
    if budget is None and factory_config and factory_config.budget:
        budget = BudgetUsage(
            max_llm_calls=factory_config.budget.max_llm_calls,
            max_tokens=factory_config.budget.max_tokens,
            used_llm_calls=0,
            used_tokens=0,
        )
    tokens = resolved_call_tokens(call)
    if budget is None:
        budget = BudgetUsage(used_llm_calls=1, used_tokens=tokens)
    else:
        budget = budget.model_copy(
            update={
                "used_llm_calls": (budget.used_llm_calls or 0) + 1,
                "used_tokens": (budget.used_tokens or 0) + tokens,
            }
        )
    writer.update_meta(budget=budget)
