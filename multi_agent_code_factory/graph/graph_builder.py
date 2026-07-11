"""LangGraph 图装配：注册节点、边与条件路由。

流水线拓扑（主路径 + 常见分支）::

    flowchart TD
        START --> pm --> prd_validate --> route_spec
        route_spec -->|pass| architect
        route_spec -->|hitl| prd_hitl --> architect
        route_spec -->|retry| pm
        architect --> design_validate --> route_design
        route_design -->|pass| developer
        route_design -->|hitl| design_hitl --> developer
        route_design -->|retry| architect
        developer --> qa --> route_qa
        route_qa -->|pass| reviewer
        route_qa -->|retry| developer
        reviewer --> route_review
        route_review -->|approved| deploy_hitl --> deploy --> END
        route_review -->|escalate| pm
        route_review -->|escalate| architect
        route_review -->|escalate| developer
        route_spec -->|limit| fail --> END
        route_spec -->|limit| escalation_hitl --> fail

``route_after_*`` 节点的精确分支逻辑见 ``graph_routing.decide_after_*``。
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from multi_agent_code_factory.graph.nodes import (
    node_architect,
    node_deploy,
    node_deploy_hitl,
    node_design_hitl,
    node_design_validate,
    node_developer,
    node_escalation_hitl,
    node_fail,
    node_pm,
    node_prd_hitl,
    node_prd_validate,
    node_qa,
    node_reviewer,
    node_route_after_design_validate,
    node_route_after_prd_validate,
    node_route_after_qa,
    node_route_after_reviewer,
)
from multi_agent_code_factory.graph.pipeline_run_context import PipelineRunContext
from multi_agent_code_factory.pipeline_nodes import (
    PipelineNode,
    conditional_route_map,
)
from multi_agent_code_factory.state import PipelineState

N = PipelineNode


def _pick_pipeline_route(state: PipelineState) -> str:
    """LangGraph 条件边选择器；读取路由节点写入的 ``pipeline_route``。"""
    return state.pipeline_route


def build_graph(*, checkpointer: Any | None = None) -> Any:
    """注册节点与边，返回编译后的 LangGraph 应用。"""
    graph = StateGraph(PipelineState, context_schema=PipelineRunContext)
    route_map = conditional_route_map()

    # --- PRD 阶段 ---
    # START → pm → prd_validate → route_after_prd_validate
    # route_after_prd_validate →? pm | prd_hitl | architect | fail | escalation_hitl
    # prd_hitl → architect（固定边）
    graph.add_node(N.PM, node_pm)
    graph.add_node(N.PRD_VALIDATE, node_prd_validate)
    graph.add_node(N.ROUTE_AFTER_PRD_VALIDATE, node_route_after_prd_validate)
    graph.add_node(N.PRD_HITL, node_prd_hitl)

    # --- Design 阶段 ---
    # architect → design_validate → route_after_design_validate
    # route_after_design_validate →?
    #   architect | design_hitl | developer | fail | escalation_hitl
    # design_hitl → developer（固定边）
    graph.add_node(N.ARCHITECT, node_architect)
    graph.add_node(N.DESIGN_VALIDATE, node_design_validate)
    graph.add_node(N.ROUTE_AFTER_DESIGN_VALIDATE, node_route_after_design_validate)
    graph.add_node(N.DESIGN_HITL, node_design_hitl)

    # --- 实现 → 测试 → 审查 ---
    # developer → qa → route_after_qa →? reviewer | developer | fail | escalation_hitl
    # reviewer → route_after_reviewer →?
    #   deploy_hitl | developer | architect | pm | fail | escalation_hitl
    graph.add_node(N.DEVELOPER, node_developer)
    graph.add_node(N.QA, node_qa)
    graph.add_node(N.ROUTE_AFTER_QA, node_route_after_qa)
    graph.add_node(N.REVIEWER, node_reviewer)
    graph.add_node(N.ROUTE_AFTER_REVIEWER, node_route_after_reviewer)

    # --- 终止路径 ---
    # deploy_hitl → deploy → END；fail → END；escalation_hitl → fail
    graph.add_node(N.DEPLOY_HITL, node_deploy_hitl)
    graph.add_node(N.DEPLOY, node_deploy)
    graph.add_node(N.FAIL, node_fail)
    graph.add_node(N.ESCALATION_HITL, node_escalation_hitl)

    graph.add_edge(START, N.PM)
    graph.add_edge(N.PM, N.PRD_VALIDATE)
    graph.add_edge(N.PRD_VALIDATE, N.ROUTE_AFTER_PRD_VALIDATE)
    graph.add_conditional_edges(
        N.ROUTE_AFTER_PRD_VALIDATE,
        _pick_pipeline_route,
        route_map,
    )
    graph.add_edge(N.PRD_HITL, N.ARCHITECT)

    graph.add_edge(N.ARCHITECT, N.DESIGN_VALIDATE)
    graph.add_edge(N.DESIGN_VALIDATE, N.ROUTE_AFTER_DESIGN_VALIDATE)
    graph.add_conditional_edges(
        N.ROUTE_AFTER_DESIGN_VALIDATE,
        _pick_pipeline_route,
        route_map,
    )
    graph.add_edge(N.DESIGN_HITL, N.DEVELOPER)

    graph.add_edge(N.DEVELOPER, N.QA)
    graph.add_edge(N.QA, N.ROUTE_AFTER_QA)
    graph.add_conditional_edges(N.ROUTE_AFTER_QA, _pick_pipeline_route, route_map)
    graph.add_edge(N.REVIEWER, N.ROUTE_AFTER_REVIEWER)
    graph.add_conditional_edges(
        N.ROUTE_AFTER_REVIEWER,
        _pick_pipeline_route,
        route_map,
    )

    graph.add_edge(N.DEPLOY_HITL, N.DEPLOY)
    graph.add_edge(N.DEPLOY, END)
    graph.add_edge(N.FAIL, END)
    graph.add_edge(N.ESCALATION_HITL, N.FAIL)

    return graph.compile(checkpointer=checkpointer)
