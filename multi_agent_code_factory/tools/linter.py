"""Execute Profile toolchain lint_command."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from multi_agent_code_factory.profiles import ProfileConfig


@dataclass(frozen=True)
class LintResult:
    passed: bool
    exit_code: int
    command: str
    stdout: str
    stderr: str


def run_linter(
    profile: ProfileConfig,
    *,
    code_root: Path | None = None,
) -> LintResult:
    command = profile.toolchain.lint_command
    if not command:
        return LintResult(
            passed=True,
            exit_code=0,
            command="",
            stdout="",
            stderr="",
        )

    cwd = (code_root or profile.code_root).resolve()
    cwd.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    )
    return LintResult(
        passed=completed.returncode == 0,
        exit_code=completed.returncode,
        command=command,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
