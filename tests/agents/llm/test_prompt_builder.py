"""LLM prompt builder tests."""

from __future__ import annotations

from multi_agent_code_factory.agent_roles import AgentRole
from multi_agent_code_factory.agents.llm.prompt.builder import build_llm_messages
from multi_agent_code_factory.profile_config import load_profile


def test_python_style_snippet_not_injected_for_pm() -> None:
    profile = load_profile("python")
    context: dict[str, object] = {"note": "test"}
    pm_system, pm_user = build_llm_messages(
        profile, role_id=AgentRole.PM, context=context, extra_system=None
    )
    assert "ruff format" not in pm_system
    assert "README.md" not in pm_system
    assert pm_user
