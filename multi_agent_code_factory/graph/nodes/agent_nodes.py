"""LangGraph Agent 节点适配。"""

from __future__ import annotations

from typing import Any

from langgraph.runtime import Runtime

from multi_agent_code_factory.agents.architect import run_architect
from multi_agent_code_factory.agents.developer import run_developer
from multi_agent_code_factory.agents.pm import run_pm
from multi_agent_code_factory.agents.qa import run_qa
from multi_agent_code_factory.agents.reviewer import run_reviewer
from multi_agent_code_factory.graph.pipeline_run_context import PipelineRunContext
from multi_agent_code_factory.state import PipelineState


def node_pm(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """PM Agent：根据 ``user_request`` 生成 spec 产物（``spec.json`` / ``spec.md``）。"""
    ctx = runtime.context
    return run_pm(
        state,
        ctx.profile,
        ctx.writer,
        stub=ctx.stub,
        stub_scenario=ctx.stub_scenario,
        llm_runner=ctx.llm_runner,
    )


def node_architect(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """Architect Agent：基于 spec 生成设计产物（``design.json`` / ``flow.mmd`` 等）。"""
    ctx = runtime.context
    return run_architect(
        state,
        ctx.profile,
        ctx.writer,
        stub=ctx.stub,
        stub_scenario=ctx.stub_scenario,
        llm_runner=ctx.llm_runner,
    )


def node_developer(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """Developer Agent：根据设计与 spec 实现代码，产出 ``dev_manifest.json``。"""
    ctx = runtime.context
    return run_developer(
        state,
        ctx.profile,
        ctx.writer,
        stub=ctx.stub,
        llm_runner=ctx.llm_runner,
    )


def node_qa(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """QA Agent：运行测试并写入 ``test_report.json``。"""
    ctx = runtime.context
    return run_qa(
        state,
        ctx.profile,
        ctx.writer,
        stub=ctx.stub,
        stub_scenario=ctx.stub_scenario,
    )


def node_reviewer(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """Reviewer Agent：评审实现质量，产出 ``review.json`` 并决定 ``next_stage``。"""
    ctx = runtime.context
    return run_reviewer(
        state,
        ctx.profile,
        ctx.writer,
        stub=ctx.stub,
        stub_scenario=ctx.stub_scenario,
        llm_runner=ctx.llm_runner,
    )
