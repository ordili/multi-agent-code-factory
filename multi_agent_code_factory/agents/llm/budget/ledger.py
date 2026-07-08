"""run_meta 预算累计写入。"""

from __future__ import annotations

from multi_agent_code_factory.agents.llm.usage.models import LlmCallUsage
from multi_agent_code_factory.config import FactoryConfig
from multi_agent_code_factory.schemas.run_meta import BudgetUsage
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter


def resolved_call_tokens(call: LlmCallUsage) -> int:
    """从单次调用记录解析 token 总数。"""
    if call.total_tokens is not None:
        return call.total_tokens
    return (call.prompt_tokens or 0) + (call.completion_tokens or 0)


def record_llm_call(
    writer: RunArtifactWriter,
    factory_config: FactoryConfig | None,
    call: LlmCallUsage,
) -> None:
    """将成功调用的次数与 token 累计写入 ``run_meta.json`` budget 字段。"""
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
