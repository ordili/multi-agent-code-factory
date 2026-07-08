"""LangGraph 流水线运行入口。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from multi_agent_code_factory.agents.base import StubScenario
from multi_agent_code_factory.agents.llm_runner import LlmRunner
from multi_agent_code_factory.config import FactoryConfig
from multi_agent_code_factory.graph.pipeline_run_context import PipelineRunContext
from multi_agent_code_factory.graph.graph_builder import build_graph
from multi_agent_code_factory.log import get_logger
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
    )
    run_context = PipelineRunContext(
        profile=profile,
        loop_limits=limits,
        writer=writer,
        stub=stub,
        stub_scenario=scenario,
        llm_runner=llm_runner,
    )
    app = build_graph()
    final_raw = app.invoke(initial, context=run_context)
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
