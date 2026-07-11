"""流水线五 Agent 节点（PM / Architect / Developer / QA / Reviewer）。"""

from __future__ import annotations

from typing import Any

__all__ = [
    "run_architect",
    "run_developer",
    "run_pm",
    "run_qa",
    "run_reviewer",
]


def __getattr__(name: str) -> Any:
    if name == "run_architect":
        from multi_agent_code_factory.agents.architect import run_architect

        return run_architect
    if name == "run_developer":
        from multi_agent_code_factory.agents.developer import run_developer

        return run_developer
    if name == "run_pm":
        from multi_agent_code_factory.agents.pm import run_pm

        return run_pm
    if name == "run_qa":
        from multi_agent_code_factory.agents.qa import run_qa

        return run_qa
    if name == "run_reviewer":
        from multi_agent_code_factory.agents.reviewer import run_reviewer

        return run_reviewer
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
