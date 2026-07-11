"""Foundry forge coverage summary 解析。"""

from __future__ import annotations

import re
from pathlib import Path

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.test_report import CoverageReport
from multi_agent_code_factory.tools.coverage_parsers._thresholds import (
    evaluate_coverage_thresholds,
    threshold_snapshot,
)
from multi_agent_code_factory.tools.coverage_parsers._types import CoverageCommandResult

_TOTAL_PERCENT = re.compile(
    r"Total.*?(\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE,
)
_LINE_PERCENT = re.compile(
    r"(\d+(?:\.\d+)?)\s*%\s*\(\s*(\d+)\s*/\s*(\d+)\s*\)",
)


def _parse_forge_summary(text: str) -> tuple[float | None, int | None, int | None]:
    for line in text.splitlines():
        if "total" not in line.lower():
            continue
        match = _TOTAL_PERCENT.search(line)
        if match:
            percent = float(match.group(1))
            counts = _LINE_PERCENT.search(line)
            if counts:
                covered = int(counts.group(2))
                total = int(counts.group(3))
                return percent, covered, total
            return percent, None, None
    match = _TOTAL_PERCENT.search(text)
    if match:
        return float(match.group(1)), None, None
    return None, None, None


def parse_forge_coverage(
    result: CoverageCommandResult,
    profile: ProfileConfig,
    code_root: Path,
) -> CoverageReport:
    del code_root
    cfg = profile.coverage
    violations: list[str] = []
    line_percent, lines_covered, lines_total = _parse_forge_summary(result.stdout)

    if line_percent is None:
        violations.append("forge coverage summary missing Total line percentage")
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

    artifact_rel = cfg.artifacts[0] if cfg.artifacts else None
    return CoverageReport(
        tool=cfg.tool or "forge-coverage",
        command=result.command,
        parser="forge_coverage",
        line_percent=line_percent,
        branch_percent=None,
        lines_covered=lines_covered,
        lines_total=lines_total,
        thresholds=threshold_snapshot(cfg.thresholds),
        passed=passed,
        violations=violations,
        raw_summary_path=artifact_rel,
    )
