"""design_hitl 图节点（MVP：需要时自动批准，不中断流水线）。"""

from __future__ import annotations

from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.hitl import HitlDecision, HitlStage
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter


def _design_hitl_required(state: PipelineState, profile: ProfileConfig) -> bool:
    if profile.validation.design.require_hitl:
        return True
    validation = state.design_validation
    return validation is not None and validation.require_hitl


def run_design_hitl(
    state: PipelineState,
    profile: ProfileConfig,
    writer: RunArtifactWriter,
) -> dict[str, object]:
    """若需要 design 人工审核则写入自动批准的 HITL 决策；否则无状态更新。"""
    if not _design_hitl_required(state, profile):
        return {}
    decision = HitlDecision(
        version="1",
        stage=HitlStage.DESIGN,
        required=True,
        reason=["profile or validation requires design HITL"],
        approved=True,
        reviewer="stub",
        comment="MVP auto-approved (no interrupt)",
    )
    writer.write_model("hitl.json", decision)
    return {"hitl": decision}
