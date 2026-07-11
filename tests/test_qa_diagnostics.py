from __future__ import annotations

import logging
from pathlib import Path

import pytest
from multi_agent_code_factory.agents.qa import run_qa
from multi_agent_code_factory.agents.stub.fixtures import StubScenario
from multi_agent_code_factory.profile_config import load_profile
from multi_agent_code_factory.schemas.test_report import (
    TestFailure,
    TestReport,
    TestSummary,
)
from multi_agent_code_factory.state import PipelineState
from multi_agent_code_factory.tools.qa_diagnostics import (
    classify_qa_block_reason,
    format_failure_details,
    log_qa_outcome,
    qa_failure_snapshot_name,
)
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter


def _report(**updates: object) -> TestReport:
    base = {
        "version": "1",
        "passed": False,
        "exit_code": 1,
        "summary": TestSummary(total=1, passed=0, failed=1, skipped=0),
        "duration_sec": 0.1,
        "command": "cargo test --message-format=json",
        "parser": "cargo_json",
        "failures": [
            TestFailure(
                test_id="calc::tests::divide_by_zero",
                message="assertion `left == right` failed",
            )
        ],
    }
    base.update(updates)
    return TestReport.model_validate(base)


def test_classify_toolchain_failure() -> None:
    report = _report()
    assert classify_qa_block_reason(report) == "toolchain"


def test_classify_tests_missing_with_profile() -> None:
    profile = load_profile("python")
    report = _report(
        passed=False,
        exit_code=0,
        summary=TestSummary(total=1, passed=1, failed=0, skipped=0),
        failures=[],
        tests_missing=["src/foo.py"],
    )
    assert classify_qa_block_reason(report, profile) == "tests_missing"


def test_classify_passed() -> None:
    report = _report(
        passed=True,
        exit_code=0,
        summary=TestSummary(total=1, passed=1, failed=0, skipped=0),
        failures=[],
    )
    assert classify_qa_block_reason(report) == "passed"


def test_format_failure_details_includes_test_id_and_message() -> None:
    details = format_failure_details(_report())
    assert "first_test='calc::tests::divide_by_zero'" in details
    assert "assertion" in details


def test_qa_failure_snapshot_name() -> None:
    assert qa_failure_snapshot_name(0) == "test_report.impl-0.json"
    assert qa_failure_snapshot_name(2) == "test_report.impl-2.json"


def test_run_qa_writes_failure_snapshot(tmp_path: Path) -> None:
    profile = load_profile("python")
    writer = RunArtifactWriter("qa-snap", base_dir=tmp_path)
    state = PipelineState(task_id="qa-snap", impl_retry_count=1)
    run_qa(
        state,
        profile,
        writer,
        stub=True,
        stub_scenario=StubScenario.QA_ALWAYS_FAIL,
    )
    snapshot_path = tmp_path / "test_report.impl-1.json"
    assert snapshot_path.is_file()
    snapshot = TestReport.model_validate_json(snapshot_path.read_text(encoding="utf-8"))
    assert snapshot.passed is False


def test_log_qa_outcome_toolchain_failure(caplog: pytest.LogCaptureFixture) -> None:
    profile = load_profile("python")
    caplog.set_level(logging.WARNING)
    log_qa_outcome(
        logging.getLogger("test.qa"),
        _report(),
        profile,
        impl_retry_count=0,
        snapshot="test_report.impl-0.json",
    )
    record = caplog.records[-1]
    assert record.levelname == "WARNING"
    assert "reason=toolchain" in record.message
    assert "first_test='calc::tests::divide_by_zero'" in record.message
    assert "snapshot=test_report.impl-0.json" in record.message
