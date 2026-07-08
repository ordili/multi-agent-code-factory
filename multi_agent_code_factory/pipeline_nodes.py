"""流水线 LangGraph 节点 ID（``add_node`` / 条件路由 / ``pipeline_route`` 共用）。"""

from __future__ import annotations

from enum import StrEnum


class PipelineNode(StrEnum):
    """LangGraph 图中各节点的唯一标识。"""

    PM = "pm"
    SPEC_VALIDATE = "spec_validate"
    ROUTE_AFTER_SPEC_VALIDATE = "route_after_spec_validate"
    SPEC_HITL = "spec_hitl"

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


# ``route_after_*`` 条件边可能跳转的目标（键与值相同，供 LangGraph 条件边映射）。
CONDITIONAL_ROUTE_TARGETS: frozenset[PipelineNode] = frozenset(
    {
        PipelineNode.PM,
        PipelineNode.SPEC_HITL,
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
