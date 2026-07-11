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
        assert "PrdArtifact" in pm
        assert "success_metrics" in pm
        assert "NOT plain strings" in pm
        assert "features:" in pm
        assert "revision" in pm
        assert "scope_in: non-empty" in pm
        assert "DesignArtifact" in architect
        assert "error_catalog" in architect
        assert "kind REQUIRED" in architect
        assert "module_ref" in architect
        assert "version" in reviewer
        assert "next_stage" in reviewer
        assert "test_report.passed" in reviewer
        assert "acceptance_coverage" in reviewer


def test_artifact_language_snippet_injected_for_audit_and_developer_roles() -> None:
    from multi_agent_code_factory.agents.llm.prompt.builder import build_llm_messages

    profile = load_profile("python")
    for role in (
        AgentRole.PM,
        AgentRole.ARCHITECT,
        AgentRole.DEVELOPER,
        AgentRole.REVIEWER,
    ):
        system_prompt, _ = build_llm_messages(
            profile, role_id=role, context={}, extra_system=None
        )
        assert "Simplified Chinese" in system_prompt
        assert "简体中文" in system_prompt


def test_developer_uses_profile_specific_prompt() -> None:
    python = load_role_prompt(load_profile("python"), AgentRole.DEVELOPER)
    go = load_role_prompt(load_profile("go"), AgentRole.DEVELOPER)
    assert "pytest" in python
    assert "go test" in go
