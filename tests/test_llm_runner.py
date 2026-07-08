"""LlmRunner provider routing tests."""

from __future__ import annotations

from multi_agent_code_factory.agents.llm import uses_prompted_json
from multi_agent_code_factory.llm import provider_spec


def test_uses_prompted_json_for_ollama_and_deepseek() -> None:
    assert uses_prompted_json("ollama") is True
    assert uses_prompted_json("deepseek") is True
    assert uses_prompted_json("openai") is False


def test_provider_spec_output_mode() -> None:
    assert provider_spec("openai").output_mode == "native_structured"
    assert provider_spec("deepseek").output_mode == "prompted_json"
