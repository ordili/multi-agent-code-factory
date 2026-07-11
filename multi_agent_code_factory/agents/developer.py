"""Developer Agent 图节点：实现代码并写入 dev_manifest。"""

from __future__ import annotations

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.base import agent_context
from multi_agent_code_factory.agents.developer_output import (
    apply_developer_output,
    merge_manifest,
)
from multi_agent_code_factory.agents.live import require_llm_runner
from multi_agent_code_factory.agents.llm import LlmRunner
from multi_agent_code_factory.agents.llm.budget.errors import LlmBudgetExceededError
from multi_agent_code_factory.agents.llm.budget.guard import check_llm_budget
from multi_agent_code_factory.agents.llm.prompt.validation_feedback import (
    format_developer_retry_extra_system,
)
from multi_agent_code_factory.agents.llm.schemas import DeveloperLLMOutput
from multi_agent_code_factory.agents.stub.fixtures import (
    default_stub_fixtures,
    load_json_fixture,
)
from multi_agent_code_factory.batch_closure import (
    BatchClosureError,
    BatchOutputError,
    format_batch_output_retry_feedback,
    validate_batch_closure,
    validate_batch_output,
)
from multi_agent_code_factory.config import FactoryConfig
from multi_agent_code_factory.dev_task_scheduler import (
    DevTaskScheduleError,
    refresh_batch_runtime,
    schedule,
)
from multi_agent_code_factory.log import agent_run, get_logger
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.prompt_context import (
    build_task_batch_context,
    resolve_impl_mode,
    task_batch_config,
)
from multi_agent_code_factory.schemas.dev_manifest import DevManifest
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter

logger = get_logger("agents.developer")


def _empty_manifest() -> DevManifest:
    return DevManifest(version="1")


def _run_developer_initial(
    state: PipelineState,
    profile: ProfileConfig,
    runner: LlmRunner,
) -> DevManifest:
    output = runner.invoke_structured(
        role_id=AgentRole.DEVELOPER,
        output_schema=DeveloperLLMOutput,
        context=agent_context(AgentRole.DEVELOPER, state, profile),
        extra_system=format_developer_retry_extra_system(state, profile),
    )
    return apply_developer_output(profile, output, patch_only=False)


def _run_developer_retry_patch(
    state: PipelineState,
    profile: ProfileConfig,
    runner: LlmRunner,
) -> DevManifest:
    output = runner.invoke_structured(
        role_id=AgentRole.DEVELOPER,
        output_schema=DeveloperLLMOutput,
        context=agent_context(AgentRole.DEVELOPER, state, profile),
        extra_system=format_developer_retry_extra_system(state, profile),
    )
    return apply_developer_output(profile, output, patch_only=True)


def _invoke_batch(
    runner: LlmRunner,
    state: PipelineState,
    profile: ProfileConfig,
    batch_context: dict,
    *,
    extra_system: str | None = None,
) -> DeveloperLLMOutput:
    merged_extra = format_developer_retry_extra_system(state, profile)
    if extra_system:
        merged_extra = (
            f"{merged_extra}\n\n{extra_system}" if merged_extra else extra_system
        )
    return runner.invoke_structured(
        role_id=AgentRole.DEVELOPER,
        output_schema=DeveloperLLMOutput,
        context=batch_context,
        extra_system=merged_extra or None,
    )


def _run_developer_task_batch(
    state: PipelineState,
    profile: ProfileConfig,
    runner: LlmRunner,
    factory_config: FactoryConfig | None,
) -> DevManifest:
    if state.design is None:
        msg = "developer task_batch requires design"
        raise ValueError(msg)

    config = task_batch_config(factory_config)
    batches = schedule(state.design, profile, config)
    manifest = state.dev_manifest or _empty_manifest()
    pass_total = len(batches)

    for batch in batches:
        batch = refresh_batch_runtime(
            batch,
            state.design,
            profile,
            config,
            code_root=profile.code_root,
        )
        batch_context = build_task_batch_context(
            state,
            profile,
            batch,
            manifest,
            pass_total=pass_total,
            factory_config=factory_config,
        )
        omitted = batch_context.get("impl_batch", {}).get("omitted_dependencies")
        try:
            validate_batch_closure(
                batch,
                manifest,
                state.design,
                profile,
                config,
                batch_context,
                omitted_dependencies=omitted if isinstance(omitted, list) else None,
            )
        except BatchClosureError as exc:
            msg = f"batch {batch.index} closure failed: {exc}"
            raise ValueError(msg) from exc

        try:
            check_llm_budget(runner.writer, factory_config)
        except LlmBudgetExceededError:
            logger.warning(
                "LLM budget exhausted before batch %s; returning partial manifest",
                batch.index,
            )
            break

        output_error: BatchOutputError | None = None
        output: DeveloperLLMOutput | None = None
        for attempt in range(2):
            extra = (
                format_batch_output_retry_feedback(output_error)
                if attempt > 0 and output_error is not None
                else None
            )
            output = _invoke_batch(
                runner,
                state,
                profile,
                batch_context,
                extra_system=extra,
            )
            try:
                validate_batch_output(output, batch, config)
                output_error = None
                break
            except BatchOutputError as exc:
                output_error = exc
                logger.warning(
                    "batch %s output validation failed (attempt %s): %s",
                    batch.index,
                    attempt + 1,
                    exc,
                )
        if output_error is not None or output is None:
            msg = f"batch {batch.index} output failed after retry: {output_error}"
            raise ValueError(msg)

        batch_manifest = apply_developer_output(
            profile,
            output,
            patch_only=True,
            skip_lint=True,
        )
        manifest = merge_manifest(manifest, batch_manifest)

    if "linter" in profile.tools:
        from multi_agent_code_factory.tools.linter import run_linter

        manifest = manifest.model_copy(
            update={"lint_passed": run_linter(profile).passed}
        )

    return manifest


def run_developer(
    state: PipelineState,
    profile: ProfileConfig,
    writer: RunArtifactWriter,
    *,
    stub: bool = True,
    llm_runner: LlmRunner | None = None,
    factory_config: FactoryConfig | None = None,
) -> dict[str, object]:
    """运行 Developer 节点，写入源码并产出 ``dev_manifest.json``。"""
    extra = {"impl_retry": state.impl_retry_count}
    with agent_run(logger, role_id=AgentRole.DEVELOPER, stub=stub, extra=extra):
        if stub:
            manifest = DevManifest.model_validate(
                load_json_fixture(default_stub_fixtures().dev_manifest)
            )
        else:
            runner = require_llm_runner(llm_runner)
            if state.prd is None or state.design is None:
                msg = "developer requires prd and design in live mode"
                raise ValueError(msg)

            effective_factory = factory_config or runner.factory_config
            impl_mode = resolve_impl_mode(state, state.design, effective_factory)

            if impl_mode == "retry_patch":
                manifest = _run_developer_retry_patch(state, profile, runner)
            elif impl_mode == "task_batch":
                try:
                    manifest = _run_developer_task_batch(
                        state,
                        profile,
                        runner,
                        effective_factory,
                    )
                except DevTaskScheduleError as exc:
                    msg = f"task_batch schedule failed: {exc}"
                    raise ValueError(msg) from exc
            else:
                manifest = _run_developer_initial(state, profile, runner)

        writer.write_model("dev_manifest.json", manifest)
    return {"dev_manifest": manifest}
