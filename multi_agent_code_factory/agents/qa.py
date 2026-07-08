"""QA Agent 图节点：执行测试并产出 test_report。"""

from __future__ import annotations

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.stub.fixtures import (
    StubScenario,
    default_stub_fixtures,
    load_json_fixture,
)
from multi_agent_code_factory.log import agent_run, get_logger
from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.test_report import TestReport
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter
from multi_agent_code_factory.tools.run_tests import run_tests

logger = get_logger("agents.qa")


def run_qa(
    state: PipelineState,
    profile: ProfileConfig,
    writer: RunArtifactWriter,
    *,
    stub: bool = True,
    stub_scenario: StubScenario = StubScenario.HAPPY,
) -> dict[str, object]:
    """运行 QA 节点，执行测试并产出 ``test_report.json``。"""
    with agent_run(logger, role_id=AgentRole.QA, stub=stub):
        if stub:
            fixtures = default_stub_fixtures()
            if stub_scenario == StubScenario.QA_ALWAYS_FAIL:
                report = TestReport.model_validate(
                    load_json_fixture(fixtures.test_report_fail)
                )
            elif stub_scenario == StubScenario.QA_FAIL_THEN_PASS:
                if state.impl_retry_count == 0:
                    report = TestReport.model_validate(
                        load_json_fixture(fixtures.test_report_fail)
                    )
                else:
                    report = TestReport.model_validate(
                        load_json_fixture(fixtures.test_report)
                    )
            else:
                report = TestReport.model_validate(
                    load_json_fixture(fixtures.test_report)
                )
        else:
            report = run_tests(profile)

        writer.write_model("test_report.json", report)
        if report.passed:
            logger.info("qa tests passed")
        else:
            logger.warning(
                "qa tests failed passed=%s failed=%s",
                report.summary.passed,
                report.summary.failed,
            )
    return {"test_report": report}
