"""Role prompt loader tests."""

from __future__ import annotations

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.prompt.loader import load_role_prompt
from multi_agent_code_factory.profile_config import load_profile


def test_language_agnostic_roles_use_shared_prompts() -> None:
    for profile_id in ("python", "go", "java"):
        profile = load_profile(profile_id)
        pm = load_role_prompt(profile, AgentRole.PM)
        architect = load_role_prompt(profile, AgentRole.ARCHITECT)
        reviewer = load_role_prompt(profile, AgentRole.REVIEWER)
        assert "SpecArtifact" in pm
        assert "DesignArtifact" in architect
        assert "test_report.passed" in reviewer


def test_developer_uses_profile_specific_prompt() -> None:
    python = load_role_prompt(load_profile("python"), AgentRole.DEVELOPER)
    go = load_role_prompt(load_profile("go"), AgentRole.DEVELOPER)
    assert "pytest" in python
    assert "go test" in go
