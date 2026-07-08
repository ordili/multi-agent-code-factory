"""LangGraph 节点适配：将 ``PipelineState`` + ``PipelineRunContext`` 桥接到业务 ``run_*``。"""

from __future__ import annotations

from typing import Any

from langgraph.runtime import Runtime

from multi_agent_code_factory.agents.architect import run_architect
from multi_agent_code_factory.agents.developer import run_developer
from multi_agent_code_factory.agents.pm import run_pm
from multi_agent_code_factory.agents.qa import run_qa
from multi_agent_code_factory.agents.reviewer import run_reviewer
from multi_agent_code_factory.graph.pipeline_run_context import PipelineRunContext
from multi_agent_code_factory.graph_routing import (
    RouteDecision,
    decide_after_design_validate,
    decide_after_review,
    decide_after_spec_validate,
    decide_after_test,
)
from multi_agent_code_factory.nodes.deploy import run_deploy
from multi_agent_code_factory.nodes.deploy_hitl import run_deploy_hitl
from multi_agent_code_factory.nodes.design_hitl import run_design_hitl
from multi_agent_code_factory.nodes.design_validate import run_design_validate
from multi_agent_code_factory.nodes.escalation_hitl import run_escalation_hitl
from multi_agent_code_factory.nodes.fail import run_fail
from multi_agent_code_factory.nodes.spec_hitl import run_spec_hitl
from multi_agent_code_factory.nodes.spec_validate import run_spec_validate
from multi_agent_code_factory.state import PipelineState


def _apply_route(
    decision: RouteDecision,
    state: PipelineState,
    ctx: PipelineRunContext,
) -> dict[str, Any]:
    """将路由决策写入 state，并更新 ``pipeline_route`` 供条件边分支。

    若决策包含 ``stale_artifacts``，则通过 writer 标记升环作废的产物文件。
    """
    if decision.stale_artifacts:
        ctx.writer.mark_stale(decision.stale_artifacts)
    return decision.apply(state)


# --- Agent 节点（Live LLM 或 stub fixture）---


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


# --- 程序校验（不调用 LLM）---


def node_spec_validate(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """规格校验：对 ``state.spec`` 执行规则校验，写入 ``spec_validation``。

    前置条件：``state.spec`` 不为空，否则抛出 ``ValueError``。
    """
    ctx = runtime.context
    profile = ctx.profile
    if state.spec is None:
        msg = "spec_validate requires spec"
        raise ValueError(msg)
    report = run_spec_validate(state.spec, profile, writer=ctx.writer)
    return {"spec_validation": report}


def node_design_validate(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """设计校验：对 ``state.design`` 执行规则校验，写入 ``design_validation``。

    前置条件：``state.design`` 不为空，否则抛出 ``ValueError``。
    """
    ctx = runtime.context
    profile = ctx.profile
    if state.design is None:
        msg = "design_validate requires design"
        raise ValueError(msg)
    report = run_design_validate(
        state.design,
        profile,
        spec=state.spec,
        writer=ctx.writer,
        run_dir=ctx.writer.directory,
    )
    return {"design_validation": report}


# --- 路由节点（设置 ``pipeline_route``，供条件边分支）---


def node_route_after_spec_validate(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """spec 校验后路由：可能前往 pm（重试）、spec_hitl、architect 或 fail/escalation_hitl。"""
    ctx = runtime.context
    decision = decide_after_spec_validate(
        state,
        ctx.profile,
        ctx.loop_limits,
    )
    return _apply_route(decision, state, ctx)


def node_route_after_design_validate(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """design 校验后路由：可能前往 architect（重试）、design_hitl、developer 或 fail/escalation_hitl。"""
    ctx = runtime.context
    decision = decide_after_design_validate(
        state,
        ctx.profile,
        ctx.loop_limits,
    )
    return _apply_route(decision, state, ctx)


def node_route_after_qa(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """QA 测试后路由：测试通过前往 reviewer，失败则重试 developer 或 fail/escalation_hitl。"""
    ctx = runtime.context
    decision = decide_after_test(state, ctx.loop_limits)
    return _apply_route(decision, state, ctx)


def node_route_after_reviewer(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """Review 后路由：批准则 deploy_hitl；否则按 ``next_stage`` 回退 pm/architect/developer。"""
    ctx = runtime.context
    decision = decide_after_review(state, ctx.loop_limits)
    return _apply_route(decision, state, ctx)


# --- HITL 占位与终止节点 ---


def node_spec_hitl(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """Spec 阶段人机协作占位（MVP：需要时自动批准，不中断流水线）。"""
    ctx = runtime.context
    return run_spec_hitl(state, ctx.profile, ctx.writer)


def node_design_hitl(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """Design 阶段人机协作占位（MVP：需要时自动批准，不中断流水线）。"""
    ctx = runtime.context
    return run_design_hitl(state, ctx.profile, ctx.writer)


def node_deploy_hitl(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """Deploy 前人机协作占位（MVP：无敏感路径/标志时跳过）。"""
    ctx = runtime.context
    return run_deploy_hitl(state, ctx.profile, ctx.writer)


def node_deploy(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """Deploy 终止节点：标记 run 为 COMPLETED 并更新 ``deploy_status``。"""
    ctx = runtime.context
    return run_deploy(state, ctx.profile, ctx.writer)


def node_fail(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """失败终止节点：记录循环上限等信息并将 run 标记为 FAILED。"""
    return run_fail(state, runtime.context.writer)


def node_escalation_hitl(
    state: PipelineState,
    *,
    runtime: Runtime[PipelineRunContext],
) -> dict[str, Any]:
    """升环 HITL 占位：循环超限且策略为 escalation_hitl 时进入，随后流向 fail。"""
    return run_escalation_hitl(state, runtime.context.writer)
