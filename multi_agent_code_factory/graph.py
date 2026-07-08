"""LangGraph 流水线装配与运行入口。

将五 Agent（PM → Architect → Developer → QA → Reviewer）、校验节点、
条件路由（重试 / 升环 / HITL）与产物写入器装配为一张图。
CLI 与测试调用 ``run_pipeline()``；编译后的图从 ``pm`` 节点开始执行。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from langgraph.graph import END, START, StateGraph

from multi_agent_code_factory.agents.architect import run_architect
from multi_agent_code_factory.agents.base import StubScenario
from multi_agent_code_factory.agents.developer import run_developer
from multi_agent_code_factory.agents.llm_runner import LlmRunner
from multi_agent_code_factory.agents.pm import run_pm
from multi_agent_code_factory.agents.qa import run_qa
from multi_agent_code_factory.agents.reviewer import run_reviewer
from multi_agent_code_factory.config import FactoryConfig, LoopLimits
from multi_agent_code_factory.graph_routing import (
    RouteDecision,
    decide_after_design_validate,
    decide_after_review,
    decide_after_spec_validate,
    decide_after_test,
)
from multi_agent_code_factory.log import get_logger
from multi_agent_code_factory.nodes.deploy import run_deploy
from multi_agent_code_factory.nodes.deploy_hitl import run_deploy_hitl
from multi_agent_code_factory.nodes.design_hitl import run_design_hitl
from multi_agent_code_factory.nodes.design_validate import run_design_validate
from multi_agent_code_factory.nodes.escalation_hitl import run_escalation_hitl
from multi_agent_code_factory.nodes.fail import run_fail
from multi_agent_code_factory.nodes.spec_hitl import run_spec_hitl
from multi_agent_code_factory.nodes.spec_validate import run_spec_validate
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.run_meta import RunStatus
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter

logger = get_logger("graph")


@dataclass
class PipelineRunResult:
    """单次 ``run_pipeline`` 调用的返回结果。"""

    state: PipelineState
    status: RunStatus
    run_dir: Path


def _pick_pipeline_route(state: PipelineState) -> str:
    """LangGraph 条件边选择器；读取路由节点写入的 ``pipeline_route``。"""
    return state.pipeline_route


@dataclass
class _GraphBindings:
    """单次 run 内各图节点共享的依赖（Profile、writer、stub/live 等）。"""

    profile: ProfileConfig
    limits: LoopLimits
    writer: RunArtifactWriter
    stub: bool
    stub_scenario: StubScenario
    llm_runner: LlmRunner | None = None

    def _require_profile(self, state: PipelineState) -> ProfileConfig:
        return state.profile or self.profile

    def _require_limits(self, state: PipelineState) -> LoopLimits:
        return state.loop_limits or self.limits

    def _route_node(
        self, decision: RouteDecision, state: PipelineState
    ) -> dict[str, Any]:
        """将路由决策写入 state；升环回路时标记作废的产物路径。"""
        if decision.stale_artifacts:
            self.writer.mark_stale(decision.stale_artifacts)
        return decision.apply(state)

    # --- Agent 节点（Live LLM 或 stub fixture）---

    def node_pm(self, state: PipelineState) -> dict[str, Any]:
        return run_pm(
            state,
            self._require_profile(state),
            self.writer,
            stub=self.stub,
            stub_scenario=self.stub_scenario,
            llm_runner=self.llm_runner,
        )

    def node_architect(self, state: PipelineState) -> dict[str, Any]:
        return run_architect(
            state,
            self._require_profile(state),
            self.writer,
            stub=self.stub,
            stub_scenario=self.stub_scenario,
            llm_runner=self.llm_runner,
        )

    def node_developer(self, state: PipelineState) -> dict[str, Any]:
        return run_developer(
            state,
            self._require_profile(state),
            self.writer,
            stub=self.stub,
            llm_runner=self.llm_runner,
        )

    def node_qa(self, state: PipelineState) -> dict[str, Any]:
        return run_qa(
            state,
            self._require_profile(state),
            self.writer,
            stub=self.stub,
            stub_scenario=self.stub_scenario,
        )

    def node_reviewer(self, state: PipelineState) -> dict[str, Any]:
        return run_reviewer(
            state,
            self._require_profile(state),
            self.writer,
            stub=self.stub,
            stub_scenario=self.stub_scenario,
            llm_runner=self.llm_runner,
        )

    # --- 程序校验（不调用 LLM）---

    def node_spec_validate(self, state: PipelineState) -> dict[str, Any]:
        profile = self._require_profile(state)
        if state.spec is None:
            msg = "spec_validate requires spec"
            raise ValueError(msg)
        report = run_spec_validate(state.spec, profile, writer=self.writer)
        return {"spec_validation": report}

    def node_design_validate(self, state: PipelineState) -> dict[str, Any]:
        profile = self._require_profile(state)
        if state.design is None:
            msg = "design_validate requires design"
            raise ValueError(msg)
        report = run_design_validate(
            state.design,
            profile,
            spec=state.spec,
            writer=self.writer,
            run_dir=self.writer.directory,
        )
        return {"design_validation": report}

    # --- 路由节点（设置 ``pipeline_route``，供条件边分支）---

    def node_route_after_spec_validate(self, state: PipelineState) -> dict[str, Any]:
        decision = decide_after_spec_validate(
            state,
            self._require_profile(state),
            self._require_limits(state),
        )
        return self._route_node(decision, state)

    def node_route_after_design_validate(self, state: PipelineState) -> dict[str, Any]:
        decision = decide_after_design_validate(
            state,
            self._require_profile(state),
            self._require_limits(state),
        )
        return self._route_node(decision, state)

    def node_route_after_qa(self, state: PipelineState) -> dict[str, Any]:
        decision = decide_after_test(state, self._require_limits(state))
        return self._route_node(decision, state)

    def node_route_after_reviewer(self, state: PipelineState) -> dict[str, Any]:
        decision = decide_after_review(state, self._require_limits(state))
        return self._route_node(decision, state)

    # --- HITL 占位与终止节点 ---

    def node_spec_hitl(self, state: PipelineState) -> dict[str, Any]:
        return run_spec_hitl(state, self._require_profile(state), self.writer)

    def node_design_hitl(self, state: PipelineState) -> dict[str, Any]:
        return run_design_hitl(state, self._require_profile(state), self.writer)

    def node_deploy_hitl(self, state: PipelineState) -> dict[str, Any]:
        return run_deploy_hitl(state, self._require_profile(state), self.writer)

    def node_deploy(self, state: PipelineState) -> dict[str, Any]:
        return run_deploy(state, self._require_profile(state), self.writer)

    def node_fail(self, state: PipelineState) -> dict[str, Any]:
        return run_fail(state, self.writer)

    def node_escalation_hitl(self, state: PipelineState) -> dict[str, Any]:
        return run_escalation_hitl(state, self.writer)


def build_graph(bindings: _GraphBindings) -> Any:
    """注册节点与边，返回编译后的 LangGraph 应用。

    主路径：pm → spec_validate → architect → design_validate → developer → qa
    → reviewer → deploy。``route_after_*`` 节点可能回路到 pm / architect / developer，
    或进入 fail / escalation_hitl。
    """
    graph = StateGraph(PipelineState)

    graph.add_node("pm", bindings.node_pm)
    graph.add_node("spec_validate", bindings.node_spec_validate)
    graph.add_node("route_after_spec_validate", bindings.node_route_after_spec_validate)
    graph.add_node("spec_hitl", bindings.node_spec_hitl)
    graph.add_node("architect", bindings.node_architect)
    graph.add_node("design_validate", bindings.node_design_validate)
    graph.add_node(
        "route_after_design_validate", bindings.node_route_after_design_validate
    )
    graph.add_node("design_hitl", bindings.node_design_hitl)
    graph.add_node("developer", bindings.node_developer)
    graph.add_node("qa", bindings.node_qa)
    graph.add_node("route_after_qa", bindings.node_route_after_qa)
    graph.add_node("reviewer", bindings.node_reviewer)
    graph.add_node("route_after_reviewer", bindings.node_route_after_reviewer)
    graph.add_node("deploy_hitl", bindings.node_deploy_hitl)
    graph.add_node("deploy", bindings.node_deploy)
    graph.add_node("fail", bindings.node_fail)
    graph.add_node("escalation_hitl", bindings.node_escalation_hitl)

    # 键名须与 graph_routing.RouteDecision 写入的 ``pipeline_route`` 一致。
    route_targets: dict[str, str] = {
        "pm": "pm",
        "spec_hitl": "spec_hitl",
        "architect": "architect",
        "design_hitl": "design_hitl",
        "developer": "developer",
        "reviewer": "reviewer",
        "deploy_hitl": "deploy_hitl",
        "fail": "fail",
        "escalation_hitl": "escalation_hitl",
    }
    route_map = cast("dict[Any, str]", route_targets)

    # Spec 阶段
    graph.add_edge(START, "pm")
    graph.add_edge("pm", "spec_validate")
    graph.add_edge("spec_validate", "route_after_spec_validate")
    graph.add_conditional_edges(
        "route_after_spec_validate",
        _pick_pipeline_route,
        route_map,
    )
    graph.add_edge("spec_hitl", "architect")

    # Design 阶段
    graph.add_edge("architect", "design_validate")
    graph.add_edge("design_validate", "route_after_design_validate")
    graph.add_conditional_edges(
        "route_after_design_validate",
        _pick_pipeline_route,
        route_map,
    )
    graph.add_edge("design_hitl", "developer")

    # 实现 → 测试 → 审查
    graph.add_edge("developer", "qa")
    graph.add_edge("qa", "route_after_qa")
    graph.add_conditional_edges("route_after_qa", _pick_pipeline_route, route_map)
    graph.add_edge("reviewer", "route_after_reviewer")
    graph.add_conditional_edges(
        "route_after_reviewer",
        _pick_pipeline_route,
        route_map,
    )

    # 终止路径
    graph.add_edge("deploy_hitl", "deploy")
    graph.add_edge("deploy", END)
    graph.add_edge("fail", END)
    graph.add_edge("escalation_hitl", "fail")

    return graph.compile()


def run_pipeline(
    *,
    task_id: str,
    user_request: str,
    profile: ProfileConfig,
    factory_config: FactoryConfig,
    run_dir: Path | None = None,
    stub: bool = True,
    stub_scenario: StubScenario | str = StubScenario.HAPPY,
) -> PipelineRunResult:
    """端到端执行一次工厂任务。

    创建 ``docs/runs/<task_id>/`` 审计目录，装配 LangGraph 并从 PM 开始 invoke。
    ``stub=True`` 使用 JSON fixture；``stub=False`` 需 ``LlmRunner``。
    """
    mode = "stub" if stub else "live"
    logger.info(
        "pipeline start task_id=%s profile=%s mode=%s",
        task_id,
        profile.id,
        mode,
    )

    # 审计目录与 run_meta.json（各节点执行过程中更新 status）。
    writer = RunArtifactWriter(task_id, base_dir=run_dir)
    limits = factory_config.loop_limits
    writer.init_run_meta(profile, limits, factory_config=factory_config)

    scenario = (
        stub_scenario
        if isinstance(stub_scenario, StubScenario)
        else StubScenario(stub_scenario)
    )

    llm_runner: LlmRunner | None = None
    if not stub:
        llm_runner = LlmRunner(writer, profile, factory_config=factory_config)

    initial = PipelineState(
        task_id=task_id,
        user_request=user_request,
        profile=profile,
        loop_limits=limits,
    )
    bindings = _GraphBindings(
        profile=profile,
        limits=limits,
        writer=writer,
        stub=stub,
        stub_scenario=scenario,
        llm_runner=llm_runner,
    )
    app = build_graph(bindings)
    final_raw = app.invoke(initial)
    if isinstance(final_raw, PipelineState):
        final_state = final_raw
    else:
        final_state = PipelineState(**final_raw)

    meta = writer.read_meta()
    status = meta.status if meta is not None else RunStatus.FAILED
    if status is None:
        status = RunStatus.FAILED
    logger.info(
        "pipeline finished task_id=%s status=%s run_dir=%s",
        task_id,
        status.value,
        writer.directory,
    )
    if meta is not None and meta.budget is not None:
        logger.info(
            "llm budget used_llm_calls=%s used_tokens=%s",
            meta.budget.used_llm_calls,
            meta.budget.used_tokens,
        )
    usage = writer.read_llm_usage()
    if usage is not None:
        logger.info(
            "llm usage totals calls=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s",
            usage.totals.llm_calls,
            usage.totals.prompt_tokens,
            usage.totals.completion_tokens,
            usage.totals.total_tokens,
        )
    return PipelineRunResult(state=final_state, status=status, run_dir=writer.directory)
