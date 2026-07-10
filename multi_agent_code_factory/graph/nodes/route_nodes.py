"""LangGraph 路由节点适配。"""

from __future__ import annotations

from typing import Any

from langgraph.runtime import Runtime

from multi_agent_code_factory.graph.nodes._routing import apply_route
from multi_agent_code_factory.graph.pipeline_run_context import PipelineRunContext
from multi_agent_code_factory.graph_routing import (
    decide_after_design_validate,
    decide_after_review,
    decide_after_spec_validate,
    decide_after_test,
)
from multi_agent_code_factory.state import PipelineState, normalize_pipeline_state


def node_route_after_spec_validate(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """spec 校验后路由。"""
    state = normalize_pipeline_state(state)
    ctx = runtime.context
    decision = decide_after_spec_validate(state, ctx.profile, ctx.loop_limits)
    return apply_route(decision, state, ctx)


def node_route_after_design_validate(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """design 校验后路由。"""
    state = normalize_pipeline_state(state)
    ctx = runtime.context
    decision = decide_after_design_validate(state, ctx.profile, ctx.loop_limits)
    return apply_route(decision, state, ctx)


def node_route_after_qa(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """QA 测试后路由。"""
    state = normalize_pipeline_state(state)
    ctx = runtime.context
    decision = decide_after_test(state, ctx.loop_limits)
    return apply_route(decision, state, ctx)


def node_route_after_reviewer(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """Review 后路由。"""
    state = normalize_pipeline_state(state)
    ctx = runtime.context
    decision = decide_after_review(state, ctx.loop_limits)
    return apply_route(decision, state, ctx)
