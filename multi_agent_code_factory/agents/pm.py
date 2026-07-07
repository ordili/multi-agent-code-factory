"""PM agent node."""

from __future__ import annotations

from multi_agent_code_factory.agents.base import (
    StubScenario,
    agent_context,
    default_stub_fixtures,
    load_json_fixture,
    load_prompt_snippet,
)
from multi_agent_code_factory.agents.live_helpers import normalize_spec
from multi_agent_code_factory.agents.llm_runner import LlmRunner
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
    _ = load_prompt_snippet(profile, "python-style-snippet.txt")

    with agent_run(logger, role_id="pm", stub=stub):
        if stub:
            fixtures = default_stub_fixtures()
            data = load_json_fixture(fixtures.spec)
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
                role_id="pm",
                schema=SpecArtifact,
                context=agent_context("pm", state, profile),
            )
            spec = normalize_spec(spec, profile, state)

        writer.write_model("spec.json", spec)
        writer.write_text("spec.md", render_spec_md(spec))
    return {"spec": spec}
