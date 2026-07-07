"""Tool registry for Developer / QA agents."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.test_report import TestReport
from multi_agent_code_factory.tools.linter import LintResult, run_linter
from multi_agent_code_factory.tools.read_file import read_file
from multi_agent_code_factory.tools.run_tests import run_tests
from multi_agent_code_factory.tools.write_file import write_file

ToolFn = Callable[..., Any]


def _wrap_read_file(profile: ProfileConfig) -> ToolFn:
    def tool(relative_path: str) -> str:
        return read_file(profile.code_root, relative_path)

    return tool


def _wrap_write_file(profile: ProfileConfig) -> ToolFn:
    def tool(relative_path: str, content: str) -> str:
        path = write_file(profile.code_root, relative_path, content)
        return str(path)

    return tool


def _wrap_run_tests(profile: ProfileConfig) -> ToolFn:
    def tool(code_root: Path | None = None) -> TestReport:
        return run_tests(profile, code_root=code_root)

    return tool


def _wrap_linter(profile: ProfileConfig) -> ToolFn:
    def tool(code_root: Path | None = None) -> LintResult:
        return run_linter(profile, code_root=code_root)

    return tool


_TOOL_BUILDERS: dict[str, Callable[[ProfileConfig], ToolFn]] = {
    "read_file": _wrap_read_file,
    "write_file": _wrap_write_file,
    "run_tests": _wrap_run_tests,
    "linter": _wrap_linter,
}


def build_tool_registry(profile: ProfileConfig) -> dict[str, ToolFn]:
    registry: dict[str, ToolFn] = {}
    for name in profile.tools:
        builder = _TOOL_BUILDERS.get(name)
        if builder is None:
            msg = f"unknown tool {name!r} for profile {profile.id!r}"
            raise ValueError(msg)
        registry[name] = builder(profile)
    return registry


def available_tools() -> tuple[str, ...]:
    return tuple(sorted(_TOOL_BUILDERS))
