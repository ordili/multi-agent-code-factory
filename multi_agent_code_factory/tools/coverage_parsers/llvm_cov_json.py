"""cargo llvm-cov JSON summary 解析。"""

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


def _as_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _as_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    return None


def _metrics_from_summary(
    summary: dict[str, Any],
) -> tuple[float | None, float | None, int | None, int | None]:
    lines = summary.get("lines")
    branches = summary.get("branches")
    line_percent = branch_percent = None
    lines_covered = lines_total = None

    if isinstance(lines, dict):
        line_percent = _as_float(lines.get("percent"))
        lines_covered = _as_int(lines.get("covered"))
        lines_total = _as_int(lines.get("count"))
    if isinstance(branches, dict):
        branch_percent = _as_float(branches.get("percent"))

    return line_percent, branch_percent, lines_covered, lines_total


def _metrics_from_payload(
    payload: dict[str, Any],
) -> tuple[float | None, float | None, int | None, int | None]:
    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            summary = item.get("summary")
            if isinstance(summary, dict):
                metrics = _metrics_from_summary(summary)
                if any(value is not None for value in metrics):
                    return metrics

    summary = payload.get("summary")
    if isinstance(summary, dict):
        return _metrics_from_summary(summary)

    totals = payload.get("totals")
    if isinstance(totals, dict):
        line_percent = _as_float(totals.get("percent"))
        lines_covered = _as_int(totals.get("covered"))
        lines_total = _as_int(totals.get("count"))
        return line_percent, None, lines_covered, lines_total

    return None, None, None, None


def parse_llvm_cov_json(
    result: CoverageCommandResult,
    profile: ProfileConfig,
    code_root: Path,
) -> CoverageReport:
    del code_root
    cfg = profile.coverage
    violations: list[str] = []
    line_percent = branch_percent = None
    lines_covered = lines_total = None

    payload: dict[str, Any] | None = None
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            violations.append("llvm-cov stdout is not valid JSON")

    if payload is None:
        violations.append("llvm-cov JSON summary unavailable in stdout")
    else:
        line_percent, branch_percent, lines_covered, lines_total = (
            _metrics_from_payload(payload)
        )
        if line_percent is None and branch_percent is None:
            violations.append("llvm-cov JSON missing line/branch summary")

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

    artifact_rel = cfg.artifacts[0] if cfg.artifacts else None
    return CoverageReport(
        tool=cfg.tool or "llvm-cov",
        command=result.command,
        parser="llvm_cov_json",
        line_percent=line_percent,
        branch_percent=branch_percent,
        lines_covered=lines_covered,
        lines_total=lines_total,
        thresholds=threshold_snapshot(cfg.thresholds),
        passed=passed,
        violations=violations,
        raw_summary_path=artifact_rel,
    )
