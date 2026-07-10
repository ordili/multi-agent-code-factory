"""Validation feedback formatter tests."""

from __future__ import annotations

from multi_agent_code_factory.agents.llm.errors import LlmParseError
from multi_agent_code_factory.agents.llm.prompt.validation_feedback import (
    format_llm_parse_retry_feedback,
)


def test_format_llm_parse_retry_feedback_includes_error() -> None:
    exc = LlmParseError("JSON did not match SpecArtifact: success_metrics.0")
    text = format_llm_parse_retry_feedback(exc)
    assert "Previous JSON output failed" in text
    assert "success_metrics.0" in text
