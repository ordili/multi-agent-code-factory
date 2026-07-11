"""Go coverprofile 解析（go tool cover -func）。"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.test_report import CoverageReport
from multi_agent_code_factory.tools.coverage_parsers._thresholds import (
    evaluate_coverage_thresholds,
    threshold_snapshot,
)
from multi_agent_code_factory.tools.coverage_parsers._types import CoverageCommandResult

_TOTAL_PERCENT = re.compile(r"(\d+(?:\.\d+)?)\s*%\s*$")


def _first_artifact(profile: ProfileConfig) -> str:
    artifacts = profile.coverage.artifacts
    if artifacts:
        return artifacts[0]
    return "coverage.out"


def _parse_go_tool_cover(code_root: Path, artifact_rel: str) -> float | None:
    artifact_path = code_root / artifact_rel
    if not artifact_path.is_file():
        return None
    completed = subprocess.run(
        f"go tool cover -func={artifact_rel}",
        cwd=code_root,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        return None
    for line in reversed(completed.stdout.splitlines()):
        stripped = line.strip()
        if not stripped.startswith("total:"):
            continue
        match = _TOTAL_PERCENT.search(stripped)
        if match:
            return float(match.group(1))
    return None


def parse_go_cover(
    result: CoverageCommandResult,
    profile: ProfileConfig,
    code_root: Path,
) -> CoverageReport:
    cfg = profile.coverage
    artifact_rel = _first_artifact(profile)
    line_percent = _parse_go_tool_cover(code_root, artifact_rel)
    violations: list[str] = []

    if line_percent is None:
        violations.append(
            f"unable to parse go coverage from {artifact_rel} (go tool cover -func)"
        )
    if result.exit_code != 0:
        violations.append(f"coverage command exit_code={result.exit_code}")

    passed, threshold_violations = evaluate_coverage_thresholds(
        line_percent=line_percent,
        branch_percent=None,
        thresholds=cfg.thresholds,
    )
    violations.extend(threshold_violations)
    if violations:
        passed = False

    return CoverageReport(
        tool=cfg.tool or "go-cover",
        command=result.command,
        parser="go_cover",
        line_percent=line_percent,
        branch_percent=None,
        lines_covered=None,
        lines_total=None,
        thresholds=threshold_snapshot(cfg.thresholds),
        passed=passed,
        violations=violations,
        raw_summary_path=artifact_rel,
    )
