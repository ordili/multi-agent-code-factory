"""JaCoCo and Foundry coverage parser tests."""

from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.profile_config.models import (
    CoverageConfig,
    CoverageThresholds,
    ProfileConfig,
    ToolchainConfig,
)
from multi_agent_code_factory.tools.coverage_parsers._types import CoverageCommandResult
from multi_agent_code_factory.tools.coverage_parsers.forge_coverage import (
    parse_forge_coverage,
)
from multi_agent_code_factory.tools.coverage_parsers.jacoco_xml import parse_jacoco_xml


def _profile(code_root: Path, *, coverage: CoverageConfig) -> ProfileConfig:
    return ProfileConfig(
        id="java",
        language="java",
        code_root=code_root,
        code_root_raw=str(code_root),
        prompts_dir=code_root,
        tools=[],
        toolchain=ToolchainConfig(test_command="true"),
        coverage=coverage,
    )


def _result(exit_code: int = 0, *, stdout: str = "") -> CoverageCommandResult:
    return CoverageCommandResult(
        exit_code=exit_code,
        stdout=stdout,
        stderr="",
        command="cov",
    )


def test_jacoco_xml_parser_sums_line_counters(tmp_path: Path) -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<report name="demo">
  <package name="com/example">
    <counter type="LINE" missed="10" covered="90"/>
  </package>
  <counter type="LINE" missed="5" covered="5"/>
</report>
"""
    artifact = tmp_path / "target" / "site" / "jacoco" / "jacoco.xml"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(xml, encoding="utf-8")

    profile = _profile(
        tmp_path,
        coverage=CoverageConfig(
            enabled=True,
            command="mvn jacoco:report",
            parser="jacoco_xml",
            artifacts=["target/site/jacoco/jacoco.xml"],
            thresholds=CoverageThresholds(line_percent=80),
        ),
    )
    report = parse_jacoco_xml(_result(), profile, tmp_path)
    assert report.lines_covered == 5
    assert report.lines_total == 10
    assert report.line_percent == 50.0
    assert report.passed is False


def test_forge_coverage_parser_reads_total_line(tmp_path: Path) -> None:
    stdout = """
| File          | % Lines       |
|---------------|---------------|
| Total         | 88.00% (22/25) |
"""
    profile = ProfileConfig(
        id="solidity",
        language="solidity",
        code_root=tmp_path,
        code_root_raw=str(tmp_path),
        prompts_dir=tmp_path,
        tools=[],
        toolchain=ToolchainConfig(test_command="true"),
        coverage=CoverageConfig(
            enabled=True,
            command="forge coverage --report summary",
            parser="forge_coverage",
            thresholds=CoverageThresholds(line_percent=70),
        ),
    )
    report = parse_forge_coverage(_result(stdout=stdout), profile, tmp_path)
    assert report.line_percent == 88.0
    assert report.lines_covered == 22
    assert report.lines_total == 25
    assert report.passed is True
