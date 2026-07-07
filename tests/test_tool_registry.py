from __future__ import annotations

from multi_agent_code_factory.profiles import load_profile
from multi_agent_code_factory.tools.registry import available_tools, build_tool_registry


def test_available_tools() -> None:
    assert "read_file" in available_tools()
    assert "run_tests" in available_tools()


def test_build_registry_for_default_profile() -> None:
    profile = load_profile("python")
    registry = build_tool_registry(profile)
    assert set(registry) == set(profile.tools)
    assert callable(registry["read_file"])
