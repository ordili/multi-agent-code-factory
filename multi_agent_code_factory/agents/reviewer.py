"""Reviewer agent node."""

from __future__ import annotations

from multi_agent_code_factory.agents.base import (
    StubScenario,
    agent_context,
    default_stub_fixtures,
    load_json_fixture,
)
from multi_agent_code_factory.agents.llm_runner import LlmRunner
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.review import ReviewReport
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter


def run_reviewer(
    state: PipelineState,
    profile: ProfileConfig,
    writer: RunArtifactWriter,
    *,
    stub: bool = True,
    stub_scenario: StubScenario = StubScenario.HAPPY,
    llm_runner: LlmRunner | None = None,
) -> dict[str, object]:
    if stub:
        fixtures = default_stub_fixtures()
        if (
            stub_scenario == StubScenario.REVIEWER_ESCALATE_ARCHITECT
            and state.design_revision_count == 0
        ):
            review = ReviewReport.model_validate(
                load_json_fixture(fixtures.review_architect)
            )
        elif (
            stub_scenario == StubScenario.REVIEWER_ESCALATE_PM
            and state.spec_revision_count == 0
        ):
            review = ReviewReport.model_validate(load_json_fixture(fixtures.review_pm))
        else:
            review = ReviewReport.model_validate(load_json_fixture(fixtures.review))
    else:
        if llm_runner is None:
            msg = "llm_runner is required when stub=False"
            raise ValueError(msg)
        review = llm_runner.invoke_structured(
            role_id="reviewer",
            schema=ReviewReport,
            context=agent_context("reviewer", state, profile),
        )

    writer.write_model("review.json", review)
    return {"review": review}
