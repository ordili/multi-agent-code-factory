"""LangGraph 校验节点适配。"""

from __future__ import annotations

from typing import Any

from langgraph.runtime import Runtime

from multi_agent_code_factory.graph.pipeline_run_context import PipelineRunContext
from multi_agent_code_factory.nodes.design_validate import run_design_validate
from multi_agent_code_factory.nodes.prd_validate import run_prd_validate
from multi_agent_code_factory.state import PipelineState


def node_prd_validate(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """PRD 校验：对 ``state.prd`` 执行规则校验，写入 ``prd_validation``。"""
    ctx = runtime.context
    profile = ctx.profile
    if state.prd is None:
        msg = "prd_validate requires prd"
        raise ValueError(msg)
    report = run_prd_validate(
        state.prd, profile, writer=ctx.writer, run_dir=ctx.writer.directory
    )
    return {"prd_validation": report}


def node_design_validate(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """设计校验：对 ``state.design`` 执行规则校验，写入 ``design_validation``。"""
    ctx = runtime.context
    profile = ctx.profile
    if state.design is None:
        msg = "design_validate requires design"
        raise ValueError(msg)
    report = run_design_validate(
        state.design,
        profile,
        spec=state.prd,
        writer=ctx.writer,
        run_dir=ctx.writer.directory,
    )
    return {"design_validation": report}
