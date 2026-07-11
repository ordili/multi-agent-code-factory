"""PM Agent 图节点：根据需求生成 prd 产物。"""

from __future__ import annotations

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.base import agent_context
from multi_agent_code_factory.agents.live import require_llm_runner
from multi_agent_code_factory.agents.llm import LlmRunner
from multi_agent_code_factory.agents.llm.prompt.validation_feedback import (
    format_prd_validation_feedback,
)
from multi_agent_code_factory.agents.normalizers.prd import normalize_prd
from multi_agent_code_factory.agents.stub.fixtures import (
    StubScenario,
    default_stub_fixtures,
    load_json_fixture,
)
from multi_agent_code_factory.log import agent_run, get_logger
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.renderers.prd_md import render_prd_md
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter

logger = get_logger("agents.pm")


def run_pm(
    state: PipelineState,
    profile: ProfileConfig,
    writer: RunArtifactWriter,
    *,
    stub: bool = True,
    stub_scenario: StubScenario = StubScenario.HAPPY,
    llm_runner: LlmRunner | None = None,
) -> dict[str, object]:
    """运行 PM 节点，产出 ``prd.json`` / ``prd.md`` 并更新 state。"""
    with agent_run(logger, role_id=AgentRole.PM, stub=stub):
        if stub:
            fixtures = default_stub_fixtures()
            data = load_json_fixture(fixtures.prd)
            if (
                stub_scenario == StubScenario.PRD_VALIDATE_RETRY
                and state.prd_revision_count == 0
            ):
                data["acceptance_criteria"] = []
            spec = PrdArtifact.model_validate(data)
        else:
            runner = require_llm_runner(llm_runner)
            spec = runner.invoke_structured(
                role_id=AgentRole.PM,
                output_schema=PrdArtifact,
                context=agent_context(AgentRole.PM, state, profile),
                extra_system=format_prd_validation_feedback(state),
            )
            spec = normalize_prd(spec, profile, state)

        writer.write_model("prd.json", spec)
        writer.write_text("prd.md", render_prd_md(spec))
    return {"prd": spec}
