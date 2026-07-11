"""LangGraph 流水线运行入口。"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from multi_agent_code_factory.agents.llm import LlmRunner
from multi_agent_code_factory.agents.qa import run_qa
from multi_agent_code_factory.agents.stub.fixtures import StubScenario
from multi_agent_code_factory.artifact_loader import hydrate_state
from multi_agent_code_factory.checkpoint import (
    GATE_REENTRY_NODES,
    ContinueError,
    infer_reentry_node,
    sqlite_checkpointer,
    validate_reentry_preconditions,
)
from multi_agent_code_factory.config import BudgetConfig, FactoryConfig, LoopLimits
from multi_agent_code_factory.graph.graph_builder import build_graph
from multi_agent_code_factory.graph.pipeline_run_context import PipelineRunContext
from multi_agent_code_factory.log import get_logger
from multi_agent_code_factory.nodes.design_validate import run_design_validate
from multi_agent_code_factory.nodes.prd_validate import run_prd_validate
from multi_agent_code_factory.observability import build_run_config, is_tracing_enabled
from multi_agent_code_factory.pipeline_nodes import PipelineNode
from multi_agent_code_factory.profile_config import ProfileConfig, load_profile
from multi_agent_code_factory.schemas.run_meta import RunMeta, RunStatus
from multi_agent_code_factory.state import (
    PipelineState,
    normalize_pipeline_state,
    state_to_graph_dict,
)
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter

logger = get_logger("graph")


@dataclass
class PipelineRunResult:
    """单次 pipeline / continue 调用的返回结果。"""

    state: PipelineState
    status: RunStatus
    run_dir: Path


def _finalize_result(
    writer: RunArtifactWriter,
    final_raw: PipelineState | dict[str, Any],
) -> PipelineRunResult:
    final_state = normalize_pipeline_state(final_raw)

    meta = writer.read_meta()
    status = meta.status if meta is not None else RunStatus.FAILED
    if status is None:
        status = RunStatus.FAILED
    return PipelineRunResult(
        state=final_state,
        status=status,
        run_dir=writer.directory,
    )


def _apply_patch(state: PipelineState, patch: dict[str, Any]) -> PipelineState:
    for key, value in patch.items():
        setattr(state, key, value)
    return state


def _profile_from_meta(
    meta: RunMeta,
    *,
    code_root_override: str | Path | None = None,
) -> ProfileConfig:
    profile_id = str(meta.profile.get("id", ""))
    if not profile_id:
        msg = "run_meta.profile.id is missing"
        raise ContinueError(msg)
    code_root = code_root_override
    if code_root is None:
        code_root = meta.profile.get("code_root")
    return load_profile(profile_id, code_root_override=code_root)


def _factory_config_from_meta(meta: RunMeta) -> FactoryConfig:
    limits = LoopLimits.model_validate(meta.loop_limits)
    budget = None
    if meta.budget is not None:
        budget = BudgetConfig(
            max_llm_calls=meta.budget.max_llm_calls,
            max_tokens=meta.budget.max_tokens,
        )
    return FactoryConfig(loop_limits=limits, budget=budget)


def _build_run_context(
    *,
    profile: ProfileConfig,
    factory_config: FactoryConfig,
    writer: RunArtifactWriter,
    stub: bool,
    stub_scenario: StubScenario,
) -> PipelineRunContext:
    llm_runner: LlmRunner | None = None
    if not stub:
        llm_runner = LlmRunner(writer, profile, factory_config=factory_config)
    return PipelineRunContext(
        profile=profile,
        loop_limits=factory_config.loop_limits,
        writer=writer,
        stub=stub,
        stub_scenario=stub_scenario,
        llm_runner=llm_runner,
    )


def _execute_gate(
    reentry: PipelineNode,
    state: PipelineState,
    ctx: PipelineRunContext,
) -> PipelineState:
    if reentry == PipelineNode.PRD_VALIDATE:
        if state.prd is None:
            msg = "prd_validate requires prd"
            raise ValueError(msg)
        report = run_prd_validate(
            state.prd,
            ctx.profile,
            writer=ctx.writer,
            run_dir=ctx.writer.directory,
        )
        return replace(state, prd_validation=report)
    if reentry == PipelineNode.DESIGN_VALIDATE:
        if state.design is None:
            msg = "design_validate requires design"
            raise ValueError(msg)
        report = run_design_validate(
            state.design,
            ctx.profile,
            spec=state.prd,
            writer=ctx.writer,
            run_dir=ctx.writer.directory,
        )
        return replace(state, design_validation=report)
    if reentry == PipelineNode.QA:
        patch = run_qa(
            state,
            ctx.profile,
            ctx.writer,
            stub=ctx.stub,
            stub_scenario=ctx.stub_scenario,
        )
        return _apply_patch(state, patch)
    msg = f"gate execution not supported for reentry {reentry!r}"
    raise ContinueError(msg)


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

    writer = RunArtifactWriter(task_id, base_dir=run_dir)
    limits = factory_config.loop_limits
    writer.init_run_meta(
        profile, limits, factory_config=factory_config, user_request=user_request
    )

    scenario = (
        stub_scenario
        if isinstance(stub_scenario, StubScenario)
        else StubScenario(stub_scenario)
    )

    run_context = _build_run_context(
        profile=profile,
        factory_config=factory_config,
        writer=writer,
        stub=stub,
        stub_scenario=scenario,
    )
    initial = PipelineState(
        task_id=task_id,
        user_request=user_request,
    )
    app = build_graph()
    run_config = build_run_config(task_id=task_id, profile_id=profile.id)
    if is_tracing_enabled():
        logger.info("langsmith tracing enabled task_id=%s", task_id)
    final_raw = app.invoke(initial, context=run_context, config=run_config)
    result = _finalize_result(writer, final_raw)
    _log_pipeline_finish(task_id, writer, result.status)
    return result


def continue_pipeline(
    *,
    task_id: str,
    run_dir: Path | None = None,
    reenter: str | None = None,
    reset_loops: bool = True,
    stub: bool = True,
    stub_scenario: StubScenario | str = StubScenario.HAPPY,
    code_root_override: str | Path | None = None,
) -> PipelineRunResult:
    """从已有 run 产物续跑：先门禁、再 invoke。"""
    writer = RunArtifactWriter(task_id, base_dir=run_dir)
    meta = writer.read_meta()
    if meta is None:
        msg = f"run_meta.json not found for task {task_id!r}; run pipeline first"
        raise ContinueError(msg)

    reentry_node = infer_reentry_node(writer.directory, meta, explicit=reenter)
    meta = writer.prepare_continue(
        reentry_node=reentry_node.value,
        reset_loops=reset_loops,
    )

    profile = _profile_from_meta(meta, code_root_override=code_root_override)
    factory_config = _factory_config_from_meta(meta)
    state = hydrate_state(writer.directory, meta)
    validate_reentry_preconditions(state, reentry_node)

    scenario = (
        stub_scenario
        if isinstance(stub_scenario, StubScenario)
        else StubScenario(stub_scenario)
    )
    run_context = _build_run_context(
        profile=profile,
        factory_config=factory_config,
        writer=writer,
        stub=stub,
        stub_scenario=scenario,
    )

    checkpointer_path = writer.directory / "checkpoint.db"
    with sqlite_checkpointer(checkpointer_path) as checkpointer:
        app = build_graph(checkpointer=checkpointer)
        run_config = build_run_config(task_id=task_id, profile_id=profile.id)
        langgraph_config = {
            **run_config,
            "configurable": {
                **run_config.get("configurable", {}),
                "thread_id": task_id,
            },
        }

        if reentry_node in GATE_REENTRY_NODES:
            state = _execute_gate(reentry_node, state, run_context)
            app.update_state(
                langgraph_config,
                state_to_graph_dict(state),
                as_node=reentry_node.value,
            )
        elif reentry_node == PipelineNode.ARCHITECT:
            state.pipeline_route = PipelineNode.ARCHITECT.value
            app.update_state(
                langgraph_config,
                state_to_graph_dict(state),
                as_node=PipelineNode.ROUTE_AFTER_PRD_VALIDATE.value,
            )
        else:
            msg = f"unsupported reentry node: {reentry_node.value}"
            raise ContinueError(msg)

        mode = "stub" if stub else "live"
        logger.info(
            "pipeline continue task_id=%s profile=%s mode=%s reentry=%s",
            task_id,
            profile.id,
            mode,
            reentry_node.value,
        )
        if is_tracing_enabled():
            logger.info("langsmith tracing enabled task_id=%s", task_id)

        final_raw = app.invoke(None, context=run_context, config=langgraph_config)
        result = _finalize_result(writer, final_raw)
        _log_pipeline_finish(task_id, writer, result.status)
        return result


def _log_pipeline_finish(
    task_id: str,
    writer: RunArtifactWriter,
    status: RunStatus,
) -> None:
    logger.info(
        "pipeline finished task_id=%s status=%s run_dir=%s",
        task_id,
        status.value,
        writer.directory,
    )
    meta = writer.read_meta()
    if meta is not None and meta.budget is not None:
        logger.info(
            "llm budget used_llm_calls=%s used_tokens=%s",
            meta.budget.used_llm_calls,
            meta.budget.used_tokens,
        )
    usage = writer.read_llm_usage()
    if usage is not None:
        logger.info(
            "llm usage totals calls=%s prompt_tokens=%s "
            "completion_tokens=%s total_tokens=%s",
            usage.totals.llm_calls,
            usage.totals.prompt_tokens,
            usage.totals.completion_tokens,
            usage.totals.total_tokens,
        )
