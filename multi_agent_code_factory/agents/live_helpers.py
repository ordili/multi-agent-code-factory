"""Post-processing helpers for live LLM agent outputs."""

from __future__ import annotations

from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.state import PipelineState


def normalize_spec(
    spec: SpecArtifact,
    profile: ProfileConfig,
    state: PipelineState,
) -> SpecArtifact:
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


def normalize_design(
    design: DesignArtifact,
    state: PipelineState,
) -> DesignArtifact:
    spec_title = state.spec.title if state.spec is not None else design.spec_ref
    revision = state.design.revision + 1 if state.design is not None else 1
    if state.design_revision_count > 0:
        revision = max(revision, state.design_revision_count + 1)
    return design.model_copy(
        update={
            "spec_ref": spec_title,
            "revision": revision,
        }
    )
