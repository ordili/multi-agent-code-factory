"""Prompted JSON strategy tests."""

from __future__ import annotations

from multi_agent_code_factory.agents.llm.strategies.prompted_json import extract_json_text


def test_extract_json_text_strips_markdown_fence() -> None:
    raw = '```json\n{"a": 1}\n```'
    assert extract_json_text(raw) == '{"a": 1}'
