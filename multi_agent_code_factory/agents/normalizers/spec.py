"""Spec 产物 Live 模式后处理。"""

from __future__ import annotations

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.state import PipelineState


def normalize_spec(
    spec: SpecArtifact,
    profile: ProfileConfig,
    state: PipelineState,
) -> SpecArtifact:
    """补全 spec 的 profile、revision 与 language 等元数据。"""
    revision = state.spec.revision + 1 if state.spec is not None else 1
    if state.spec_revision_count > 0:
        revision = max(revision, state.spec_revision_count + 1)
    context = dict(spec.context)
    if profile.language:
        context["language"] = profile.language
    return spec.model_copy(
        update={
            "profile": profile.id,
            "revision": revision,
            "context": context,
        }
    )
