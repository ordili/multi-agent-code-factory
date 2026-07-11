"""prd_hitl ????MVP?????????????????"""

from __future__ import annotations

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.hitl import HitlDecision, HitlStage
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter


def _prd_hitl_required(state: PipelineState, profile: ProfileConfig) -> bool:
    if profile.validation.prd.require_hitl:
        return True
    validation = state.prd_validation
    return validation is not None and validation.require_hitl


def run_prd_hitl(
    state: PipelineState,
    profile: ProfileConfig,
    writer: RunArtifactWriter,
) -> dict[str, object]:
    """??? prd ???????????? HITL ???????????"""
    if not _prd_hitl_required(state, profile):
        return {}
    decision = HitlDecision(
        version="1",
        stage=HitlStage.PRD,
        required=True,
        reason=["profile or validation requires prd HITL"],
        approved=True,
        reviewer="stub",
        comment="MVP auto-approved (no interrupt)",
    )
    writer.write_model("hitl.json", decision)
    return {"hitl": decision}
