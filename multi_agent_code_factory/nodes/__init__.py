"""非 LLM 图节点：校验、HITL 占位与 deploy 终止。"""

from __future__ import annotations

from typing import Any

__all__ = [
    "run_deploy",
    "run_deploy_hitl",
    "run_design_hitl",
    "run_design_validate",
    "run_escalation_hitl",
    "run_fail",
    "run_prd_hitl",
    "run_prd_validate",
]


def __getattr__(name: str) -> Any:
    if name == "run_deploy":
        from multi_agent_code_factory.nodes.deploy import run_deploy

        return run_deploy
    if name == "run_deploy_hitl":
        from multi_agent_code_factory.nodes.deploy_hitl import run_deploy_hitl

        return run_deploy_hitl
    if name == "run_design_hitl":
        from multi_agent_code_factory.nodes.design_hitl import run_design_hitl

        return run_design_hitl
    if name == "run_design_validate":
        from multi_agent_code_factory.nodes.design_validate import run_design_validate

        return run_design_validate
    if name == "run_escalation_hitl":
        from multi_agent_code_factory.nodes.escalation_hitl import run_escalation_hitl

        return run_escalation_hitl
    if name == "run_fail":
        from multi_agent_code_factory.nodes.fail import run_fail

        return run_fail
    if name == "run_prd_hitl":
        from multi_agent_code_factory.nodes.prd_hitl import run_prd_hitl

        return run_prd_hitl
    if name == "run_prd_validate":
        from multi_agent_code_factory.nodes.prd_validate import run_prd_validate

        return run_prd_validate
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
