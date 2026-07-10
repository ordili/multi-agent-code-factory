"""Validation feedback formatter tests."""

from __future__ import annotations

from multi_agent_code_factory.agents.llm.errors import LlmParseError
from multi_agent_code_factory.agents.llm.prompt.validation_feedback import (
    format_llm_parse_retry_feedback,
    format_spec_validation_feedback,
)
from multi_agent_code_factory.schemas.validation_report import (
    ValidationReport,
    ValidationTarget,
)
from multi_agent_code_factory.state import PipelineState


def test_format_llm_parse_retry_feedback_includes_error() -> None:
    exc = LlmParseError("JSON did not match SpecArtifact: success_metrics.0")
    text = format_llm_parse_retry_feedback(exc)
    assert "Previous JSON output failed" in text
    assert "success_metrics.0" in text


def test_format_spec_validation_feedback_none_when_passed() -> None:
    report = ValidationReport(
        version="1",
        target=ValidationTarget.SPEC,
        passed=True,
        error_count=0,
        warn_count=0,
        violations=[],
    )
    state = PipelineState(user_request="x", spec_validation=report)
    assert format_spec_validation_feedback(state) is None
