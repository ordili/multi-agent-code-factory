"""Agent prompt 上下文：各角色 watch 列表、prompt 组装与 Developer 重试包。"""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.config import FactoryConfig
from multi_agent_code_factory.dependency_extract import extract_dependency_artifacts
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.prompt_context_trim import (
    trim_context_for_role,
    trim_design_for_task_batch,
    trim_dev_manifest_for_batch,
    trim_prd,
)
from multi_agent_code_factory.retry_context import build_failure_contexts
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.dev_manifest import DevManifest
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.schemas.retry_context import (
    RetryBundle,
    RetryCause,
    ReviewFeedback,
)
from multi_agent_code_factory.schemas.review import ReviewNextStage, ReviewReport
from multi_agent_code_factory.schemas.task_batch import (
    ImplBatch,
    TaskBatch,
    TaskBatchConfig,
)
from multi_agent_code_factory.schemas.test_report import TestReport
from multi_agent_code_factory.schemas.validation_report import ValidationReport
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.task_batch_context import (
    fit_task_batch_context_to_input_budget,
)

DEFAULT_WATCH: dict[AgentRole, list[str]] = {
    AgentRole.PM: ["user_request", "profile", "prd_validation", "review"],
    AgentRole.ARCHITECT: [
        "prd",
        "profile",
        "review",
        "test_report",
        "design_validation",
    ],
    AgentRole.DEVELOPER: ["prd", "design", "profile"],
    AgentRole.QA: ["design", "dev_manifest", "profile"],
    AgentRole.REVIEWER: ["prd", "design", "test_report", "dev_manifest"],
    AgentRole.DEPLOY_HITL: ["review", "design", "dev_manifest", "profile"],
    AgentRole.ESCALATION_HITL: [
        "run_meta",
        "impl_retry_count",
        "design_revision_count",
        "prd_revision_count",
        "test_report",
        "review",
        "prd_validation",
        "design_validation",
    ],
    AgentRole.DEPLOY: ["review", "hitl", "profile"],
}


def resolve_watch(role_id: AgentRole, profile: ProfileConfig) -> list[str]:
    """解析角色应订阅的状态字段（Profile 覆盖优先于默认 watch）。"""
    subscriptions = profile.subscriptions or {}
    override = subscriptions.get(role_id)
    if override is not None:
        return list(override)
    return list(DEFAULT_WATCH.get(role_id, []))


def _resolve_retry_cause(state: PipelineState) -> RetryCause | None:
    qa_failed = state.test_report is not None and not state.test_report.passed
    review_rejected = (
        state.review is not None
        and not state.review.approved
        and state.review.next_stage == ReviewNextStage.DEVELOPER
    )
    if qa_failed and review_rejected:
        return "both"
    if qa_failed:
        return "qa_failure"
    if review_rejected:
        return "review_rejection"
    return None


def build_retry_bundle(
    state: PipelineState,
    profile: ProfileConfig,
) -> RetryBundle | None:
    """为 Developer 重试组装测试失败、review 反馈与 failure_contexts。"""
    if state.impl_retry_count <= 0:
        return None
    if state.dev_manifest is None:
        return None

    retry_cause = _resolve_retry_cause(state)
    if retry_cause is None and state.test_report is None:
        return None

    reflection = None
    if state.dev_manifest.reflection is not None:
        reflection = state.dev_manifest.reflection.model_dump(mode="json")

    review_feedback: ReviewFeedback | None = None
    review_findings = None
    if state.review is not None and not state.review.approved:
        review_feedback = ReviewFeedback(
            approved=state.review.approved,
            summary=state.review.summary,
            findings=list(state.review.findings),
        )
        review_findings = list(state.review.findings)

    failure_contexts, omitted_paths = build_failure_contexts(
        test_report=state.test_report,
        language=profile.language,
        code_root=profile.code_root,
        design=state.design,
        dev_manifest=state.dev_manifest,
        review_findings=review_findings,
    )

    return RetryBundle(
        retry_cause=retry_cause or "qa_failure",
        test_report=state.test_report,
        review_feedback=review_feedback,
        dev_manifest=state.dev_manifest,
        reflection=reflection,
        failure_contexts=failure_contexts,
        code_snippets_omitted_paths=omitted_paths,
    )


def task_batch_config(factory_config: FactoryConfig | None) -> TaskBatchConfig:
    if factory_config is None:
        return TaskBatchConfig()
    return factory_config.task_batch


def should_task_batch(
    design: DesignArtifact,
    factory_config: FactoryConfig | None,
) -> bool:
    """判定首轮是否走 task_batch。"""
    config = task_batch_config(factory_config)
    if config.enabled:
        return True
    return len(design.dev_tasks) > config.threshold


def resolve_impl_mode(
    state: PipelineState,
    design: DesignArtifact | None,
    factory_config: FactoryConfig | None,
) -> str:
    if state.impl_retry_count > 0:
        return "retry_patch"
    if design is not None and should_task_batch(design, factory_config):
        return "task_batch"
    return "initial"


def build_task_batch_context(
    state: PipelineState,
    profile: ProfileConfig,
    batch: TaskBatch,
    manifest: DevManifest,
    *,
    pass_total: int,
    factory_config: FactoryConfig | None = None,
) -> dict[str, Any]:
    """组装单批 Developer prompt 上下文。"""
    if state.prd is None or state.design is None:
        msg = "task_batch requires prd and design"
        raise ValueError(msg)

    config = task_batch_config(factory_config)
    by_id = {task.id: task for task in state.design.dev_tasks}
    active_tasks = [by_id[task_id] for task_id in batch.task_ids if task_id in by_id]

    dep_artifacts, omitted = extract_dependency_artifacts(
        batch.dependency_paths,
        profile,
        max_lines=config.dep_snippet_lines,
    )
    relevant_cases = [
        case
        for case in state.design.test_cases
        if case.id in batch.relevant_test_case_ids
    ]

    impl_batch = ImplBatch(
        pass_index=batch.index + 1,
        pass_total=pass_total,
        active_dev_tasks=active_tasks,
        completed_dev_tasks=list(manifest.tasks_completed),
        required_paths=batch.required_paths,
        dependency_artifacts=dep_artifacts,
        relevant_test_cases=relevant_cases,
        omitted_dependencies=omitted,
    )

    context: dict[str, Any] = {
        "profile": {
            "id": profile.id,
            "language": profile.language,
            "code_root": str(profile.code_root),
        },
        "prd": trim_prd(state.prd.model_dump(mode="json")),
        "design": trim_design_for_task_batch(
            state.design.model_dump(mode="json"),
            batch,
            active_tasks,
            completed_task_ids=manifest.tasks_completed,
        ),
        "impl_mode": "task_batch",
        "impl_batch": impl_batch.model_dump(mode="json"),
        "dev_manifest": trim_dev_manifest_for_batch(manifest.model_dump(mode="json")),
    }

    from multi_agent_code_factory.agents.llm.prompt.validation_feedback import (
        format_semantic_advisories,
    )

    prd_advisories = format_semantic_advisories(
        state.prd_validation,
        headline=(
            "PRD semantic validation advisories "
            "(address before downstream work when possible):"
        ),
    )
    if prd_advisories:
        context["semantic_advisories_prd"] = prd_advisories

    design_advisories = format_semantic_advisories(
        state.design_validation,
        headline=(
            "Design semantic validation advisories "
            "(address before implementation when possible):"
        ),
    )
    if design_advisories:
        context["semantic_advisories_design"] = design_advisories

    if profile.auto_generate_tests:
        context["auto_generate_tests"] = True

    return fit_task_batch_context_to_input_budget(
        context,
        config.max_input_lines_per_batch,
    )


def build_prompt_context(
    role_id: AgentRole,
    state: PipelineState,
    profile: ProfileConfig,
) -> dict[str, Any]:
    """按角色 watch 列表从 PipelineState 组装 prompt 上下文。"""
    context: dict[str, Any] = {}
    for key in resolve_watch(role_id, profile):
        if key == "user_request":
            context[key] = state.user_request
        elif key == "profile":
            context[key] = {
                "id": profile.id,
                "language": profile.language,
                "code_root": str(profile.code_root),
            }
        elif key == "run_meta":
            context[key] = {
                "task_id": state.task_id,
                "impl_retry_count": state.impl_retry_count,
                "design_revision_count": state.design_revision_count,
                "prd_revision_count": state.prd_revision_count,
            }
        elif key == "impl_retry_count":
            context[key] = state.impl_retry_count
        elif key == "design_revision_count":
            context[key] = state.design_revision_count
        elif key == "prd_revision_count":
            context[key] = state.prd_revision_count
        else:
            value = getattr(state, key, None)
            if isinstance(
                value,
                (
                    PrdArtifact,
                    DesignArtifact,
                    DevManifest,
                    TestReport,
                    ReviewReport,
                    ValidationReport,
                ),
            ):
                context[key] = value.model_dump(mode="json")
            elif value is not None:
                context[key] = value

    if role_id in {AgentRole.ARCHITECT, AgentRole.DEVELOPER, AgentRole.REVIEWER}:
        from multi_agent_code_factory.agents.llm.prompt.validation_feedback import (
            format_semantic_advisories,
        )

        prd_advisories = format_semantic_advisories(
            state.prd_validation,
            headline=(
                "PRD semantic validation advisories "
                "(address before downstream work when possible):"
            ),
        )
        if prd_advisories:
            context["semantic_advisories_prd"] = prd_advisories

    if role_id in {AgentRole.DEVELOPER, AgentRole.REVIEWER}:
        design_advisories = format_semantic_advisories(
            state.design_validation,
            headline=(
                "Design semantic validation advisories "
                "(address before implementation when possible):"
            ),
        )
        if design_advisories:
            context["semantic_advisories_design"] = design_advisories

    if role_id == AgentRole.DEVELOPER:
        context["impl_mode"] = resolve_impl_mode(
            state,
            state.design,
            None,
        )
        bundle = build_retry_bundle(state, profile)
        if bundle is not None:
            context["retry_bundle"] = bundle.model_dump(mode="json")
        if profile.auto_generate_tests:
            context["auto_generate_tests"] = True
        if state.test_report is not None and state.test_report.tests_missing:
            context["tests_missing"] = list(state.test_report.tests_missing)

    if role_id == AgentRole.REVIEWER:
        if state.test_report is not None and state.test_report.acceptance_traceability:
            context["acceptance_traceability"] = [
                item.model_dump(mode="json")
                for item in state.test_report.acceptance_traceability
            ]
        from multi_agent_code_factory.tools.git_diff import git_diff

        diff_paths: list[str] | None = None
        if state.dev_manifest is not None:
            diff_paths = [
                item.path for item in state.dev_manifest.changed_files if item.path
            ]
        diff = git_diff(profile.code_root, paths=diff_paths or None)
        if diff:
            context["git_diff"] = diff

    return trim_context_for_role(role_id, context)
