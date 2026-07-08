"""LlmRunner provider routing tests."""

from __future__ import annotations

from multi_agent_code_factory.agents.llm import uses_prompted_json


def test_uses_prompted_json_for_ollama_and_deepseek() -> None:
    assert uses_prompted_json("ollama") is True
    assert uses_prompted_json("deepseek") is True
    assert uses_prompted_json("openai") is False
