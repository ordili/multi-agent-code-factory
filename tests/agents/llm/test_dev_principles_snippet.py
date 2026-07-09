"""Dev principles snippet loading tests."""

from __future__ import annotations

import pytest
from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.prompt.builder import build_llm_messages
from multi_agent_code_factory.agents.llm.prompt.style_snippet import (
    load_dev_principles_snippet,
)
from multi_agent_code_factory.profile_config import load_profile


def test_load_dev_principles_snippet_exists() -> None:
    text = load_dev_principles_snippet()
    assert text is not None
    assert "README.md" in text
    assert "Single responsibility" in text


def test_developer_gets_dev_principles_and_language_snippet() -> None:
    profile = load_profile("python")
    dev_system, _ = build_llm_messages(
        profile,
        role_id=AgentRole.DEVELOPER,
        context={"note": "test"},
        extra_system=None,
    )
    assert "README.md" in dev_system
    assert "ruff format" in dev_system


def test_pm_does_not_get_dev_principles_snippet() -> None:
    profile = load_profile("python")
    pm_system, _ = build_llm_messages(
        profile,
        role_id=AgentRole.PM,
        context={"note": "test"},
        extra_system=None,
    )
    assert "README.md" not in pm_system


@pytest.mark.parametrize(
    ("profile_id", "marker"),
    [
        ("python", "ruff format"),
        ("go", "golangci-lint run"),
        ("java", "mvn -q checkstyle:check"),
        ("rust", "cargo clippy"),
        ("solidity", "checks-effects-interactions"),
    ],
)
def test_developer_gets_language_style_snippet(profile_id: str, marker: str) -> None:
    profile = load_profile(profile_id)
    dev_system, _ = build_llm_messages(
        profile,
        role_id=AgentRole.DEVELOPER,
        context={"note": "test"},
        extra_system=None,
    )
    assert "README.md" in dev_system
    assert marker in dev_system
