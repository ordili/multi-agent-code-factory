"""Profile style snippet path tests."""

from __future__ import annotations

from multi_agent_code_factory.agents.llm.prompt.style_snippet import style_snippet_path
from multi_agent_code_factory.profile_config import load_profile


def test_style_snippet_path_resolves_per_language() -> None:
    assert style_snippet_path(load_profile("python")).name == "python-style-snippet.txt"
    assert style_snippet_path(load_profile("go")).name == "go-style-snippet.txt"
    assert style_snippet_path(load_profile("java")).name == "java-style-snippet.txt"
    assert style_snippet_path(load_profile("rust")).name == "rust-style-snippet.txt"
    assert (
        style_snippet_path(load_profile("solidity")).name
        == "solidity-style-snippet.txt"
    )
