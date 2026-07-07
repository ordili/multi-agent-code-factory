"""escalation_hitl graph node (loop limit placeholder)."""

from __future__ import annotations

from multi_agent_code_factory.schemas.hitl import HitlDecision, HitlStage
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter


def run_escalation_hitl(
    state: PipelineState,
    writer: RunArtifactWriter,
) -> dict[str, object]:
    decision = HitlDecision(
        version="1",
        stage=HitlStage.ESCALATION,
        required=True,
        reason=["loop limit exceeded"],
        approved=False,
        reviewer="stub",
        comment="MVP escalation placeholder",
    )
    writer.write_model("hitl.json", decision)
    return {"hitl": decision}
