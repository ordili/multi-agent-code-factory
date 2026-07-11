"""Spec 产物 Live 模式后处理。"""

from __future__ import annotations

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.state import PipelineState


def normalize_prd(
    prd: PrdArtifact,
    profile: ProfileConfig,
    state: PipelineState,
) -> PrdArtifact:
    """补全 spec 的 profile、revision 与 language 等元数据。"""
    revision = state.prd.revision + 1 if state.prd is not None else 1
    if state.prd_revision_count > 0:
        revision = max(revision, state.prd_revision_count + 1)
    context = dict(prd.context)
    if profile.language:
        context["language"] = profile.language
    return prd.model_copy(
        update={
            "profile": profile.id,
            "revision": revision,
            "context": context,
        }
    )
