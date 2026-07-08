"""LLM prompt builder tests."""

from __future__ import annotations

import pytest

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.prompt.builder import build_llm_messages
from multi_agent_code_factory.profile_config import load_profile


@pytest.mark.parametrize(
    ("profile_id", "marker"),
    [
        ("python", "Single responsibility"),
        ("go", "golangci-lint run"),
        ("java", "mvn -q checkstyle:check"),
        ("rust", "cargo clippy"),
        ("solidity", "checks-effects-interactions"),
    ],
)
def test_developer_gets_language_style_snippet(profile_id: str, marker: str) -> None:
    profile = load_profile(profile_id)
    context: dict[str, object] = {"note": "test"}
    dev_system, _ = build_llm_messages(
        profile, role_id=AgentRole.DEVELOPER, context=context, extra_system=None
    )
    assert marker in dev_system


def test_python_style_snippet_not_injected_for_pm() -> None:
    profile = load_profile("python")
    context: dict[str, object] = {"note": "test"}
    pm_system, pm_user = build_llm_messages(
        profile, role_id=AgentRole.PM, context=context, extra_system=None
    )
    assert "Single responsibility" not in pm_system
    assert pm_user
