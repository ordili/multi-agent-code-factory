"""JaCoCo XML 覆盖率报告解析。"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

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
    return "target/site/jacoco/jacoco.xml"


def _line_counters(root: ET.Element) -> tuple[int, int]:
    covered = missed = 0
    direct = [
        counter
        for counter in root.findall("counter")
        if counter.attrib.get("type") == "LINE"
    ]
    if direct:
        for counter in direct:
            covered += int(counter.attrib.get("covered", 0))
            missed += int(counter.attrib.get("missed", 0))
        return covered, missed

    for package in root.findall("package"):
        for counter in package.findall("counter"):
            if counter.attrib.get("type") != "LINE":
                continue
            covered += int(counter.attrib.get("covered", 0))
            missed += int(counter.attrib.get("missed", 0))
    return covered, missed


def parse_jacoco_xml(
    result: CoverageCommandResult,
    profile: ProfileConfig,
    code_root: Path,
) -> CoverageReport:
    cfg = profile.coverage
    artifact_rel = _first_artifact(profile)
    artifact_path = code_root / artifact_rel
    violations: list[str] = []
    line_percent = branch_percent = None
    lines_covered = lines_total = None

    if not artifact_path.is_file():
        violations.append(f"coverage artifact missing: {artifact_rel}")
    else:
        try:
            root = ET.parse(artifact_path).getroot()
            covered, missed = _line_counters(root)
            lines_covered = covered
            lines_total = covered + missed
            if lines_total > 0:
                line_percent = round(100.0 * covered / lines_total, 2)
        except ET.ParseError:
            violations.append(f"coverage artifact invalid XML: {artifact_rel}")

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
        tool=cfg.tool or "jacoco",
        command=result.command,
        parser="jacoco_xml",
        line_percent=line_percent,
        branch_percent=branch_percent,
        lines_covered=lines_covered,
        lines_total=lines_total,
        thresholds=threshold_snapshot(cfg.thresholds),
        passed=passed,
        violations=violations,
        raw_summary_path=artifact_rel,
    )
