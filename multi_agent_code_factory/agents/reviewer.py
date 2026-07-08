"""Reviewer Agent 图节点：审查产物并决定下一跳路由。"""

from __future__ import annotations

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.base import agent_context
from multi_agent_code_factory.agents.live import require_llm_runner
from multi_agent_code_factory.agents.llm import LlmRunner
from multi_agent_code_factory.agents.stub.fixtures import (
    StubScenario,
    default_stub_fixtures,
    load_json_fixture,
)
from multi_agent_code_factory.log import agent_run, get_logger
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.renderers.review_md import render_review_md
from multi_agent_code_factory.schemas.review import ReviewReport
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter

logger = get_logger("agents.reviewer")


def run_reviewer(
    state: PipelineState,
    profile: ProfileConfig,
    writer: RunArtifactWriter,
    *,
    stub: bool = True,
    stub_scenario: StubScenario = StubScenario.HAPPY,
    llm_runner: LlmRunner | None = None,
) -> dict[str, object]:
    """运行 Reviewer 节点，产出 ``review.json`` / ``review.md``。"""
    with agent_run(logger, role_id=AgentRole.REVIEWER, stub=stub):
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
                review = ReviewReport.model_validate(
                    load_json_fixture(fixtures.review_pm)
                )
            else:
                review = ReviewReport.model_validate(load_json_fixture(fixtures.review))
        else:
            runner = require_llm_runner(llm_runner)
            review = runner.invoke_structured(
                role_id=AgentRole.REVIEWER,
                output_schema=ReviewReport,
                context=agent_context(AgentRole.REVIEWER, state, profile),
            )

        writer.write_model("review.json", review)
        writer.write_text("review.md", render_review_md(review))
        logger.info(
            "review outcome approved=%s next_stage=%s",
            review.approved,
            review.next_stage.value,
        )
    return {"review": review}
