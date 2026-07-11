"""Coverage 阈值判定（Profile → CoverageReport.passed）。"""

from __future__ import annotations

from multi_agent_code_factory.profile_config.models import CoverageThresholds
from multi_agent_code_factory.schemas.test_report import CoverageThresholdSnapshot


def threshold_snapshot(
    thresholds: CoverageThresholds,
) -> CoverageThresholdSnapshot | None:
    if thresholds.line_percent is None and thresholds.branch_percent is None:
        return None
    return CoverageThresholdSnapshot(
        line_percent=thresholds.line_percent,
        branch_percent=thresholds.branch_percent,
    )


def evaluate_coverage_thresholds(
    *,
    line_percent: float | None,
    branch_percent: float | None,
    thresholds: CoverageThresholds,
) -> tuple[bool, list[str]]:
    """相对 Profile 阈值计算 coverage.passed 与 violations。"""
    violations: list[str] = []
    has_threshold = (
        thresholds.line_percent is not None or thresholds.branch_percent is not None
    )
    if not has_threshold:
        return True, violations

    if thresholds.line_percent is not None:
        if line_percent is None:
            violations.append(
                f"line coverage unavailable (threshold {thresholds.line_percent}%)"
            )
        elif line_percent < thresholds.line_percent:
            violations.append(
                f"line {line_percent:.1f}% < threshold {thresholds.line_percent}%"
            )

    if thresholds.branch_percent is not None:
        if branch_percent is None:
            violations.append(
                f"branch coverage unavailable (threshold {thresholds.branch_percent}%)"
            )
        elif branch_percent < thresholds.branch_percent:
            violations.append(
                f"branch {branch_percent:.1f}% < threshold {thresholds.branch_percent}%"
            )

    return not violations, violations
