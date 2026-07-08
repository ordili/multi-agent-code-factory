"""Design 产物 Live 模式后处理。"""

from __future__ import annotations

from multi_agent_code_factory.agents.normalizers.design_enrichment import enrich_design_for_validation
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.state import PipelineState


def normalize_design(
    design: DesignArtifact,
    state: PipelineState,
) -> DesignArtifact:
    """规范化 design 的 revision、spec_ref，并补全校验缺口。"""
    spec_title = state.spec.title if state.spec is not None else design.spec_ref
    revision = state.design.revision + 1 if state.design is not None else 1
    if state.design_revision_count > 0:
        revision = max(revision, state.design_revision_count + 1)
    enriched = enrich_design_for_validation(design, spec=state.spec)
    return enriched.model_copy(
        update={
            "spec_ref": spec_title,
            "revision": revision,
        }
    )
