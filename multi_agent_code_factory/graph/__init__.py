"""LangGraph 流水线装配与运行入口。

将五 Agent（PM → Architect → Developer → QA → Reviewer）、校验节点、
条件路由（重试 / 升环 / HITL）与产物写入器装配为一张图。
CLI 与测试调用 ``run_pipeline()`` / ``continue_pipeline()``。
"""

from multi_agent_code_factory.checkpoint import ContinueError
from multi_agent_code_factory.graph.graph_builder import build_graph
from multi_agent_code_factory.graph.runner import (
    PipelineRunResult,
    continue_pipeline,
    run_pipeline,
)

__all__ = [
    "ContinueError",
    "PipelineRunResult",
    "build_graph",
    "continue_pipeline",
    "run_pipeline",
]
