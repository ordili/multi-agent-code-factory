"""LangGraph run 级上下文：单次 invoke 共享的依赖与配置。"""

from __future__ import annotations

from dataclasses import dataclass

from multi_agent_code_factory.agents.base import StubScenario
from multi_agent_code_factory.agents.llm_runner import LlmRunner
from multi_agent_code_factory.config import LoopLimits
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter


@dataclass(frozen=True, slots=True)
class PipelineRunContext:
    """单次 pipeline run 的共享依赖（通过 ``invoke(..., context=...)`` 注入）。"""

    profile: ProfileConfig
    loop_limits: LoopLimits
    writer: RunArtifactWriter
    stub: bool
    stub_scenario: StubScenario
    llm_runner: LlmRunner | None = None
