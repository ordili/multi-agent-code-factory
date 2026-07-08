"""Live 模式 Agent 共享辅助。"""

from __future__ import annotations

from multi_agent_code_factory.agents.llm import LlmRunner


def require_llm_runner(llm_runner: LlmRunner | None) -> LlmRunner:
    """Live 模式下校验 ``llm_runner`` 已注入。"""
    if llm_runner is None:
        msg = "llm_runner is required when stub=False"
        raise ValueError(msg)
    return llm_runner
