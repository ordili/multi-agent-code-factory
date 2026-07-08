"""PM Agent 图节点：根据需求生成 spec 产物。"""

from __future__ import annotations

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.base import (
    StubScenario,
    agent_context,
    default_stub_fixtures,
    load_json_fixture,
)
from multi_agent_code_factory.agents.artifact_normalizers import normalize_spec
from multi_agent_code_factory.agents.llm import LlmRunner
from multi_agent_code_factory.log import agent_run, get_logger
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.renderers.spec_md import render_spec_md
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter

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
    """运行 PM 节点，产出 ``spec.json`` / ``spec.md`` 并更新 state。"""
    with agent_run(logger, role_id=AgentRole.PM, stub=stub):
        if stub:
            fixtures = default_stub_fixtures()
            data = load_json_fixture(fixtures.spec)
            # 首次修订时清空验收标准，触发 spec_validate 重试路径
            if (
                stub_scenario == StubScenario.SPEC_VALIDATE_RETRY
                and state.spec_revision_count == 0
            ):
                data["acceptance_criteria"] = []
            spec = SpecArtifact.model_validate(data)
        else:
            if llm_runner is None:
                msg = "llm_runner is required when stub=False"
                raise ValueError(msg)
            spec = llm_runner.invoke_structured(
                role_id=AgentRole.PM,
                output_schema=SpecArtifact,
                context=agent_context(AgentRole.PM, state, profile),
            )
            spec = normalize_spec(spec, profile, state)

        writer.write_model("spec.json", spec)
        writer.write_text("spec.md", render_spec_md(spec))
    return {"spec": spec}
