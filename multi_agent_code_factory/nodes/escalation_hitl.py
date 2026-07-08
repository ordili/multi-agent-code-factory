"""escalation_hitl 图节点：环路超限时的 HITL 占位。"""

from __future__ import annotations

from multi_agent_code_factory.schemas.hitl import HitlDecision, HitlStage
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter


def run_escalation_hitl(
    state: PipelineState,
    writer: RunArtifactWriter,
) -> dict[str, object]:
    """写入未批准的升环 HITL 决策，供后续 fail 节点消费。"""
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
