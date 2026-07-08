"""Agent prompt 上下文：各角色 watch 列表、prompt 组装与 Developer 重试包。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.prompt_context_trim import trim_context_for_role
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.dev_manifest import DevManifest
from multi_agent_code_factory.schemas.review import ReviewReport
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.schemas.test_report import TestReport
from multi_agent_code_factory.schemas.validation_report import ValidationReport
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.read_file import read_file

DEFAULT_WATCH: dict[AgentRole, list[str]] = {
    AgentRole.PM: ["user_request", "profile", "spec_validation", "review"],
    AgentRole.ARCHITECT: [
        "spec",
        "profile",
        "review",
        "test_report",
        "design_validation",
    ],
    AgentRole.DEVELOPER: ["spec", "design", "profile"],
    AgentRole.QA: ["design", "dev_manifest", "profile"],
    AgentRole.REVIEWER: ["spec", "design", "test_report", "dev_manifest"],
    AgentRole.DEPLOY_HITL: ["review", "design", "dev_manifest", "profile"],
    AgentRole.ESCALATION_HITL: [
        "run_meta",
        "impl_retry_count",
        "design_revision_count",
        "spec_revision_count",
        "test_report",
        "review",
        "spec_validation",
        "design_validation",
    ],
    AgentRole.DEPLOY: ["review", "hitl", "profile"],
}


class CodeSnippet(BaseModel):
    path: str
    content: str


class RetryBundle(BaseModel):
    spec: SpecArtifact
    design: DesignArtifact
    test_report: TestReport
    dev_manifest: DevManifest
    reflection: dict[str, Any] | None = None
    code_snippets: list[CodeSnippet] = Field(default_factory=list)


def resolve_watch(role_id: AgentRole, profile: ProfileConfig) -> list[str]:
    """解析角色应订阅的状态字段（Profile 覆盖优先于默认 watch）。"""
    subscriptions = profile.subscriptions or {}
    override = subscriptions.get(role_id)
    if override is not None:
        return list(override)
    return list(DEFAULT_WATCH.get(role_id, []))


def _read_code_snippets(
    failures: list[Any],
    *,
    code_root: Path,
) -> list[CodeSnippet]:
    snippets: list[CodeSnippet] = []
    seen: set[str] = set()
    for failure in failures:
        file_path = getattr(failure, "file", None)
        if not isinstance(file_path, str) or not file_path or file_path in seen:
            continue
        seen.add(file_path)
        try:
            content = read_file(code_root, file_path)
        except (OSError, ValueError):
            continue
        snippets.append(CodeSnippet(path=file_path, content=content))
    return snippets


def build_retry_bundle(
    state: PipelineState,
    profile: ProfileConfig,
) -> RetryBundle | None:
    """为 Developer 重试组装规格、设计、测试失败与代码片段。"""
    if state.impl_retry_count <= 0:
        return None
    if (
        state.spec is None
        or state.design is None
        or state.test_report is None
        or state.dev_manifest is None
    ):
        return None
    reflection = None
    if state.dev_manifest.reflection is not None:
        reflection = state.dev_manifest.reflection.model_dump(mode="json")
    return RetryBundle(
        spec=state.spec,
        design=state.design,
        test_report=state.test_report,
        dev_manifest=state.dev_manifest,
        reflection=reflection,
        code_snippets=_read_code_snippets(
            state.test_report.failures,
            code_root=profile.code_root,
        ),
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
                "spec_revision_count": state.spec_revision_count,
            }
        elif key == "impl_retry_count":
            context[key] = state.impl_retry_count
        elif key == "design_revision_count":
            context[key] = state.design_revision_count
        elif key == "spec_revision_count":
            context[key] = state.spec_revision_count
        else:
            value = getattr(state, key, None)
            if isinstance(
                value,
                (
                    SpecArtifact,
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

    if role_id == AgentRole.DEVELOPER:
        bundle = build_retry_bundle(state, profile)
        if bundle is not None:
            context["retry_bundle"] = bundle.model_dump(mode="json")

    return trim_context_for_role(role_id, context)
