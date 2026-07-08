"""JUnit XML 测试报告解析器（支持 pytest、Maven Surefire 等）。"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.test_report import (
    TestFailure,
    TestReport,
    TestSummary,
)
from multi_agent_code_factory.tools.test_parsers._types import CommandResult

_OUTPUT_TAIL_LIMIT = 4000


def _artifact_paths(code_root: Path, patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(sorted(code_root.glob(pattern)))
    return paths


def _parse_int(value: str | None, default: int = 0) -> int:
    if value is None or value == "":
        return default
    return int(value)


def _suite_metrics(suite: ET.Element) -> tuple[int, int, int, int]:
    tests = _parse_int(suite.attrib.get("tests"))
    failures = _parse_int(suite.attrib.get("failures"))
    errors = _parse_int(suite.attrib.get("errors"))
    skipped = _parse_int(suite.attrib.get("skipped"))
    failed = failures + errors
    passed = max(tests - failed - skipped, 0)
    return tests, passed, failed, skipped


def _collect_failures(suite: ET.Element, failures: list[TestFailure]) -> None:
    for case in suite.findall("testcase"):
        failure = case.find("failure")
        error = case.find("error")
        node = failure if failure is not None else error
        if node is None:
            continue
        classname = case.attrib.get("classname", "")
        name = case.attrib.get("name", "")
        test_id = f"{classname}::{name}" if classname else name
        line_raw = case.attrib.get("line")
        line = int(line_raw) if line_raw and line_raw.isdigit() else None
        file_path = case.attrib.get("file")
        message = node.attrib.get("message") or (node.text or "").strip()
        failures.append(
            TestFailure(
                test_id=test_id or "unknown",
                suite=classname or None,
                name=name or None,
                file=file_path,
                line=line,
                message=message or "test failed",
                output=(node.text or "").strip() or None,
            )
        )


def _aggregate_from_xml(path: Path) -> tuple[TestSummary, list[TestFailure]]:
    root = ET.parse(path).getroot()
    suites: list[ET.Element]
    if root.tag == "testsuites":
        suites = root.findall("testsuite")
    elif root.tag == "testsuite":
        suites = [root]
    else:
        msg = f"unsupported junit root element: {root.tag}"
        raise ValueError(msg)

    total = passed = failed = skipped = 0
    failures: list[TestFailure] = []
    for suite in suites:
        s_total, s_passed, s_failed, s_skipped = _suite_metrics(suite)
        total += s_total
        passed += s_passed
        failed += s_failed
        skipped += s_skipped
        _collect_failures(suite, failures)

    return (
        TestSummary(total=total, passed=passed, failed=failed, skipped=skipped),
        failures,
    )


def parse_junit_xml(
    result: CommandResult,
    profile: ProfileConfig,
    code_root: Path,
) -> TestReport:
    """解析 JUnit XML 产物并汇总为 TestReport；无产物时退化为退出码判断。"""
    artifact_patterns = profile.toolchain.test_artifacts
    artifact_files = _artifact_paths(code_root, artifact_patterns)

    if artifact_files:
        # 聚合多个 XML 产物
        summary = TestSummary(total=0, passed=0, failed=0, skipped=0)
        failures: list[TestFailure] = []
        for path in artifact_files:
            part_summary, part_failures = _aggregate_from_xml(path)
            summary = TestSummary(
                total=summary.total + part_summary.total,
                passed=summary.passed + part_summary.passed,
                failed=summary.failed + part_summary.failed,
                skipped=summary.skipped + part_summary.skipped,
            )
            failures.extend(part_failures)
        passed = result.exit_code == 0 and summary.failed == 0 and not failures
    else:
        # 未找到 XML 产物，仅依据退出码
        passed = result.exit_code == 0
        summary = TestSummary(
            total=0,
            passed=0,
            failed=0 if passed else 1,
            skipped=0,
        )
        failures = []
        if not passed:
            failures.append(
                TestFailure(
                    test_id="junit_xml_missing",
                    message="test artifacts not found for junit_xml parser",
                )
            )

    return TestReport(
        version="1",
        passed=passed,
        exit_code=result.exit_code,
        summary=summary,
        failures=failures,
        duration_sec=result.duration_sec,
        command=result.command,
        parser="junit_xml",
        language=profile.language,
        raw_output_tail=(result.stderr or result.stdout or "")[-_OUTPUT_TAIL_LIMIT:]
        if not passed
        else None,
    )
