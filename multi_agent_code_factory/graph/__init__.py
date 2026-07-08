"""LangGraph 流水线装配与运行入口。

将五 Agent（PM → Architect → Developer → QA → Reviewer）、校验节点、
条件路由（重试 / 升环 / HITL）与产物写入器装配为一张图。
CLI 与测试调用 ``run_pipeline()``；编译后的图从 ``pm`` 节点开始执行。
"""

from multi_agent_code_factory.graph.runner import PipelineRunResult, run_pipeline
from multi_agent_code_factory.graph.graph_builder import build_graph

__all__ = ["PipelineRunResult", "build_graph", "run_pipeline"]
