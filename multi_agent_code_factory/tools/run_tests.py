"""Execute Profile toolchain test_command and produce TestReport."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.test_report import TestReport
from multi_agent_code_factory.tools.test_parsers._types import CommandResult
from multi_agent_code_factory.tools.test_parsers.registry import get_parser


def _run_shell(command: str, cwd: Path) -> CommandResult:
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    )
    duration = time.perf_counter() - started
    return CommandResult(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_sec=duration,
        command=command,
    )


def run_tests(
    profile: ProfileConfig,
    *,
    code_root: Path | None = None,
) -> TestReport:
    """Run setup/build/test_command under code_root and parse output."""
    cwd = (code_root or profile.code_root).resolve()
    cwd.mkdir(parents=True, exist_ok=True)

    toolchain = profile.toolchain
    if toolchain.setup:
        setup = _run_shell(toolchain.setup, cwd)
        if setup.exit_code != 0:
            parser = get_parser("exit_code_only")
            return parser(setup, profile, cwd)

    if toolchain.build:
        build = _run_shell(toolchain.build, cwd)
        if build.exit_code != 0:
            parser = get_parser("exit_code_only")
            return parser(build, profile, cwd)

    test_result = _run_shell(toolchain.test_command, cwd)
    parser = get_parser(toolchain.test_parser)
    return parser(test_result, profile, cwd)
