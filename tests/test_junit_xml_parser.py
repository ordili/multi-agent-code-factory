from __future__ import annotations

from pathlib import Path

from multi_agent_code_factory.profile_config import ProfileConfig, ToolchainConfig
from multi_agent_code_factory.tools.test_parsers._types import CommandResult
from multi_agent_code_factory.tools.test_parsers.junit_xml import parse_junit_xml


def _profile_with_junit(artifacts: list[str]) -> ProfileConfig:
    return ProfileConfig(
        id="test",
        code_root=Path("."),
        code_root_raw=".",
        prompts_dir=Path("."),
        tools=[],
        toolchain=ToolchainConfig(
            test_command="pytest",
            test_parser="junit_xml",
            test_artifacts=artifacts,
        ),
    )


def test_junit_xml_parser_reads_failures(tmp_path: Path) -> None:
    fixture = Path(__file__).parent / "fixtures" / "junit_fail.xml"
    reports = tmp_path / "reports"
    reports.mkdir()
    target = reports / "junit.xml"
    target.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")

    profile = _profile_with_junit(["reports/junit.xml"])
    profile = profile.model_copy(update={"code_root": tmp_path})

    report = parse_junit_xml(
        CommandResult(
            exit_code=1,
            stdout="",
            stderr="",
            duration_sec=0.5,
            command="pytest",
        ),
        profile,
        tmp_path,
    )
    assert report.passed is False
    assert report.summary.failed == 1
    assert len(report.failures) == 1
    assert report.failures[0].test_id == "tests.test_sample::test_fail"
    assert report.failures[0].file == "tests/test_sample.py"
    assert report.failures[0].line == 5


def test_junit_xml_parser_all_pass(tmp_path: Path) -> None:
    xml = """<?xml version="1.0" encoding="utf-8"?>
<testsuite tests="1" failures="0" errors="0" skipped="0">
  <testcase
    classname="tests.test_ok"
    name="test_pass"
    file="tests/test_ok.py"
    line="2"
  />
</testsuite>
"""
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "junit.xml").write_text(xml, encoding="utf-8")

    profile = _profile_with_junit(["reports/junit.xml"])
    profile = profile.model_copy(update={"code_root": tmp_path})

    report = parse_junit_xml(
        CommandResult(0, "", "", 0.2, "pytest"),
        profile,
        tmp_path,
    )
    assert report.passed is True
    assert report.summary.total == 1
    assert report.failures == []
