"""LangGraph HITL 与终止节点适配。"""

from __future__ import annotations

from typing import Any

from langgraph.runtime import Runtime

from multi_agent_code_factory.graph.pipeline_run_context import PipelineRunContext
from multi_agent_code_factory.nodes.deploy import run_deploy
from multi_agent_code_factory.nodes.deploy_hitl import run_deploy_hitl
from multi_agent_code_factory.nodes.design_hitl import run_design_hitl
from multi_agent_code_factory.nodes.escalation_hitl import run_escalation_hitl
from multi_agent_code_factory.nodes.fail import run_fail
from multi_agent_code_factory.nodes.prd_hitl import run_prd_hitl
from multi_agent_code_factory.state import PipelineState, normalize_pipeline_state


def _state(state: PipelineState) -> PipelineState:
    return normalize_pipeline_state(state)


def node_prd_hitl(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """Spec 阶段人机协作占位。"""
    state = _state(state)
    ctx = runtime.context
    return run_prd_hitl(state, ctx.profile, ctx.writer)


def node_design_hitl(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """Design 阶段人机协作占位。"""
    state = _state(state)
    ctx = runtime.context
    return run_design_hitl(state, ctx.profile, ctx.writer)


def node_deploy_hitl(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """Deploy 前人机协作占位。"""
    state = _state(state)
    ctx = runtime.context
    return run_deploy_hitl(state, ctx.profile, ctx.writer)


def node_deploy(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """Deploy 终止节点。"""
    state = _state(state)
    ctx = runtime.context
    return run_deploy(state, ctx.profile, ctx.writer)


def node_fail(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """失败终止节点。"""
    state = _state(state)
    return run_fail(state, runtime.context.writer)


def node_escalation_hitl(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """升环 HITL 占位。"""
    state = _state(state)
    return run_escalation_hitl(state, runtime.context.writer)
