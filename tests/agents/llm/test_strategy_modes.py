"""Strategy output-mode and provider mapping tests."""

from __future__ import annotations

from multi_agent_code_factory.agents.llm.strategies.modes import (
    NATIVE_STRUCTURED_PROVIDERS,
    PROMPTED_JSON_PROVIDERS,
)
from multi_agent_code_factory.agents.llm.strategies.native_structured import (
    NativeStructuredStrategy,
)
from multi_agent_code_factory.agents.llm.strategies.prompted_json import (
    PromptedJsonStrategy,
)


def test_native_structured_strategy_documents_openai_and_anthropic() -> None:
    assert NativeStructuredStrategy.supported_providers == ("anthropic", "openai")
    assert NATIVE_STRUCTURED_PROVIDERS == ("anthropic", "openai")


def test_prompted_json_strategy_documents_deepseek_and_ollama() -> None:
    assert PromptedJsonStrategy.supported_providers == ("deepseek", "ollama")
    assert PROMPTED_JSON_PROVIDERS == ("deepseek", "ollama")
