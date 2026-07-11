"""Agent prompt 上下文：各角色 watch 列表、prompt 组装与 Developer 重试包。"""

from __future__ import annotations

from typing import Any

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.prompt_context_trim import trim_context_for_role
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
from multi_agent_code_factory.schemas.test_report import TestReport
from multi_agent_code_factory.schemas.validation_report import ValidationReport
from multi_agent_code_factory.state import PipelineState

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
        if state.impl_retry_count > 0:
            context["impl_mode"] = "retry_patch"
        else:
            context["impl_mode"] = "initial"
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
