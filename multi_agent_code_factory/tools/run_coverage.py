"""执行 Profile.coverage 命令并解析为 CoverageReport。"""

from __future__ import annotations

import subprocess
from pathlib import Path

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.test_report import CoverageReport
from multi_agent_code_factory.tools.coverage_parsers._types import CoverageCommandResult
from multi_agent_code_factory.tools.coverage_parsers.registry import get_coverage_parser


def _run_shell(command: str, cwd: Path) -> CoverageCommandResult:
    completed = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return CoverageCommandResult(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        command=command,
    )


def run_coverage(
    profile: ProfileConfig,
    *,
    code_root: Path,
) -> CoverageReport | None:
    """在 code_root 下执行 coverage 命令并解析；未启用时返回 None。"""
    cfg = profile.coverage
    if not cfg.enabled or not cfg.command:
        return None

    cwd = code_root.resolve()
    result = _run_shell(cfg.command, cwd)
    parser = get_coverage_parser(cfg.parser)
    return parser(result, profile, cwd)
