"""pytest-cov JSON 报告解析。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from multi_agent_code_factory.profile_config import ProfileConfig
from multi_agent_code_factory.schemas.test_report import CoverageReport
from multi_agent_code_factory.tools.coverage_parsers._thresholds import (
    evaluate_coverage_thresholds,
    threshold_snapshot,
)
from multi_agent_code_factory.tools.coverage_parsers._types import CoverageCommandResult


def _first_artifact(profile: ProfileConfig) -> str:
    artifacts = profile.coverage.artifacts
    if artifacts:
        return artifacts[0]
    return "coverage.json"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _metrics_from_totals(
    totals: dict[str, Any],
) -> tuple[float | None, float | None, int | None, int | None]:
    line_percent = totals.get("percent_covered")
    if isinstance(line_percent, (int, float)):
        line_percent = float(line_percent)
    else:
        line_percent = None

    branch_percent = totals.get("percent_covered_branches")
    if isinstance(branch_percent, (int, float)):
        branch_percent = float(branch_percent)
    else:
        branch_percent = None

    lines_covered = totals.get("covered_lines")
    lines_total = totals.get("num_statements")
    covered = int(lines_covered) if isinstance(lines_covered, int) else None
    total = int(lines_total) if isinstance(lines_total, int) else None
    return line_percent, branch_percent, covered, total


def parse_pytest_cov_json(
    result: CoverageCommandResult,
    profile: ProfileConfig,
    code_root: Path,
) -> CoverageReport:
    cfg = profile.coverage
    artifact_rel = _first_artifact(profile)
    artifact_path = code_root / artifact_rel
    payload = _read_json(artifact_path)

    line_percent = branch_percent = None
    lines_covered = lines_total = None
    violations: list[str] = []

    if payload is None:
        violations.append(f"coverage artifact missing or invalid: {artifact_rel}")
    else:
        totals = payload.get("totals")
        if isinstance(totals, dict):
            line_percent, branch_percent, lines_covered, lines_total = (
                _metrics_from_totals(totals)
            )
        else:
            violations.append(f"coverage artifact missing totals: {artifact_rel}")

    if result.exit_code != 0:
        violations.append(f"coverage command exit_code={result.exit_code}")

    passed, threshold_violations = evaluate_coverage_thresholds(
        line_percent=line_percent,
        branch_percent=branch_percent,
        thresholds=cfg.thresholds,
    )
    violations.extend(threshold_violations)
    if violations:
        passed = False

    return CoverageReport(
        tool=cfg.tool or "pytest-cov",
        command=result.command,
        parser="pytest_cov_json",
        line_percent=line_percent,
        branch_percent=branch_percent,
        lines_covered=lines_covered,
        lines_total=lines_total,
        thresholds=threshold_snapshot(cfg.thresholds),
        passed=passed,
        violations=violations,
        raw_summary_path=artifact_rel,
    )
