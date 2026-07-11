"""Validation feedback formatter tests."""

from __future__ import annotations

from multi_agent_code_factory.agents.llm.errors import LlmParseError
from multi_agent_code_factory.agents.llm.prompt.validation_feedback import (
    format_llm_parse_retry_feedback,
    format_prd_validation_feedback,
    format_qa_retry_feedback,
    format_semantic_advisories,
)
from multi_agent_code_factory.schemas.test_report import TestFailure, TestSummary
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    ValidationTarget,
    Violation,
    ViolationSeverity,
)
from multi_agent_code_factory.state import PipelineState


def test_format_llm_parse_retry_feedback_includes_error() -> None:
    exc = LlmParseError("JSON did not match PrdArtifact: success_metrics.0")
    text = format_llm_parse_retry_feedback(exc)
    assert "Previous JSON output failed" in text
    assert "success_metrics.0" in text


def test_format_prd_validation_feedback_none_when_passed() -> None:
    report = ValidationReport(
        version="1",
        target=ValidationTarget.PRD,
        passed=True,
        error_count=0,
        warn_count=0,
        violations=[],
    )
    state = PipelineState(user_request="x", prd_validation=report)
    assert format_prd_validation_feedback(state) is None


def test_format_qa_retry_feedback_lists_tests_missing_and_failures() -> None:
    from multi_agent_code_factory.schemas.test_report import TestReport

    report = TestReport(
        version="1",
        passed=False,
        exit_code=0,
        summary=TestSummary(total=2, passed=1, failed=1, skipped=0),
        duration_sec=1.0,
        command="pytest",
        parser="junit_xml",
        tests_missing=["src/cli.py"],
        failures=[
            TestFailure(
                test_id="tests.test_cli::test_bad",
                message="AssertionError",
                file="tests/test_cli.py",
            )
        ],
    )
    state = PipelineState(
        user_request="calc",
        impl_retry_count=1,
        test_report=report,
    )

    feedback = format_qa_retry_feedback(state)

    assert feedback is not None
    assert "tests_missing" in feedback
    assert "src/cli.py" in feedback
    assert "tests.test_cli::test_bad" in feedback
    assert "pytest summary" in feedback


def test_format_qa_retry_feedback_none_on_first_run() -> None:
    state = PipelineState(user_request="x", impl_retry_count=0)
    assert format_qa_retry_feedback(state) is None


def test_format_semantic_advisories_when_passed_with_warn() -> None:
    report = ValidationReport(
        version="1",
        target=ValidationTarget.PRD,
        passed=True,
        error_count=0,
        warn_count=1,
        violations=[
            Violation(
                rule_id="PRD-S01",
                severity=ViolationSeverity.WARN,
                message="semantic_constraints missing",
            )
        ],
    )
    text = format_semantic_advisories(
        report,
        headline="PRD semantic advisories:",
    )
    assert text is not None
    assert "PRD-S01" in text
    assert "semantic_constraints missing" in text
