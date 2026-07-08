"""LangGraph 路由节点共享辅助。"""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.graph.pipeline_run_context import PipelineRunContext
from multi_agent_code_factory.graph_routing import RouteDecision
from multi_agent_code_factory.state import PipelineState


def apply_route(
    decision: RouteDecision,
    state: PipelineState,
    ctx: PipelineRunContext,
) -> dict[str, Any]:
    """将路由决策写入 state，并更新 ``pipeline_route`` 供条件边分支。"""
    if decision.stale_artifacts:
        ctx.writer.mark_stale(decision.stale_artifacts)
    return decision.apply(state)
