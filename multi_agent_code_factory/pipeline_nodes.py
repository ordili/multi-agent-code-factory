"""流水线 LangGraph 节点 ID（``add_node`` / 条件路由 / ``pipeline_route`` 共用）。"""

from __future__ import annotations

from enum import StrEnum


class PipelineNode(StrEnum):
    """LangGraph 图中各节点的唯一标识。"""

    PM = "pm"
    PRD_VALIDATE = "prd_validate"
    ROUTE_AFTER_PRD_VALIDATE = "route_after_prd_validate"
    PRD_HITL = "prd_hitl"

    ARCHITECT = "architect"
    DESIGN_VALIDATE = "design_validate"
    ROUTE_AFTER_DESIGN_VALIDATE = "route_after_design_validate"
    DESIGN_HITL = "design_hitl"

    DEVELOPER = "developer"

    QA = "qa"
    ROUTE_AFTER_QA = "route_after_qa"

    REVIEWER = "reviewer"
    ROUTE_AFTER_REVIEWER = "route_after_reviewer"

    DEPLOY_HITL = "deploy_hitl"
    DEPLOY = "deploy"

    FAIL = "fail"
    ESCALATION_HITL = "escalation_hitl"


CONDITIONAL_ROUTE_TARGETS: frozenset[PipelineNode] = frozenset(
    {
        PipelineNode.PM,
        PipelineNode.PRD_HITL,
        PipelineNode.ARCHITECT,
        PipelineNode.DESIGN_HITL,
        PipelineNode.DEVELOPER,
        PipelineNode.REVIEWER,
        PipelineNode.DEPLOY_HITL,
        PipelineNode.FAIL,
        PipelineNode.ESCALATION_HITL,
    }
)


def conditional_route_map() -> dict[str, str]:
    """构建 ``add_conditional_edges`` 使用的路由表。"""
    return {node: node for node in CONDITIONAL_ROUTE_TARGETS}
