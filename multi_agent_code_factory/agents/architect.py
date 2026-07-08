"""Architect Agent 图节点：根据 spec 生成设计与流程图。"""

from __future__ import annotations

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.base import agent_context
from multi_agent_code_factory.agents.live import require_llm_runner
from multi_agent_code_factory.agents.llm import LlmRunner
from multi_agent_code_factory.agents.llm.prompt.validation_feedback import (
    format_design_validation_feedback,
)
from multi_agent_code_factory.agents.llm.schemas import ArchitectLLMOutput
from multi_agent_code_factory.agents.normalizers.design import normalize_design
from multi_agent_code_factory.agents.stub.fixtures import (
    StubScenario,
    default_stub_fixtures,
    load_json_fixture,
)
from multi_agent_code_factory.log import agent_run, get_logger
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.renderers.design_md import render_design_md
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter

logger = get_logger("agents.architect")


def run_architect(
    state: PipelineState,
    profile: ProfileConfig,
    writer: RunArtifactWriter,
    *,
    stub: bool = True,
    stub_scenario: StubScenario = StubScenario.HAPPY,
    llm_runner: LlmRunner | None = None,
) -> dict[str, object]:
    """运行 Architect 节点，产出 ``design.json`` / ``flow.mmd`` / ``design.md``。"""
    extra = {"revision": state.design_revision_count}
    with agent_run(logger, role_id=AgentRole.ARCHITECT, stub=stub, extra=extra):
        if stub:
            fixtures = default_stub_fixtures()
            if (
                stub_scenario == StubScenario.DESIGN_VALIDATE_RETRY
                and state.design_revision_count == 0
            ):
                data = load_json_fixture(fixtures.design_invalid)
            else:
                data = load_json_fixture(fixtures.design)
            design = DesignArtifact.model_validate(data)
            flow_text = fixtures.flow_mmd.read_text(encoding="utf-8")
        else:
            runner = require_llm_runner(llm_runner)
            if state.spec is None:
                msg = "architect requires spec in live mode"
                raise ValueError(msg)
            output = runner.invoke_structured(
                role_id=AgentRole.ARCHITECT,
                output_schema=ArchitectLLMOutput,
                context=agent_context(AgentRole.ARCHITECT, state, profile),
                extra_system=format_design_validation_feedback(state),
            )
            design = normalize_design(output.design, state)
            flow_text = output.flow_mmd

        writer.write_model("design.json", design)
        writer.write_text("flow.mmd", flow_text)
        writer.write_text("design.md", render_design_md(design))
    return {"design": design}
